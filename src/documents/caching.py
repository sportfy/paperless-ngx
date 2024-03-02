import logging
from binascii import hexlify
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Final
from typing import Optional

from django.core.cache import cache

from documents.models import Document

if TYPE_CHECKING:
    from documents.classifier import DocumentClassifier

logger = logging.getLogger("paperless.caching")


@dataclass(frozen=True)
class MetadataCacheData:
    original_checksum: str
    original_metadata: list
    archive_checksum: Optional[str]
    archive_metadata: Optional[list]


@dataclass(frozen=True)
class SuggestionCacheData:
    classifier_version: int
    classifier_hash: str
    suggestions: dict


CLASSIFIER_VERSION_KEY: Final[str] = "classifier_version"
CLASSIFIER_HASH_KEY: Final[str] = "classifier_hash"
CLASSIFIER_MODIFIED_KEY: Final[str] = "classifier_modified"

CACHE_1_MINUTE: Final[int] = 60
CACHE_5_MINUTES: Final[int] = 5 * CACHE_1_MINUTE
CACHE_50_MINUTES: Final[int] = 50 * CACHE_1_MINUTE


def get_suggestion_cache_key(document_id: int) -> str:
    """
    Returns the basic key for a document's suggestions
    """
    return f"doc_{document_id}_suggest"


def get_suggestion_cache(document_id: int) -> Optional[SuggestionCacheData]:
    """
    If possible, return the cached suggestions for the given document ID.
    The classifier needs to be matching in format and hash and the suggestions need to
    have been cached once.
    """
    from documents.classifier import DocumentClassifier

    doc_key = get_suggestion_cache_key(document_id)
    cache_hits = cache.get_many([CLASSIFIER_VERSION_KEY, CLASSIFIER_HASH_KEY, doc_key])
    # The document suggestions are in the cache
    if doc_key in cache_hits:
        doc_suggestions: SuggestionCacheData = cache_hits[doc_key]
        # The classifier format is the same
        # The classifier hash is the same
        # Then the suggestions can be used
        if (
            CLASSIFIER_VERSION_KEY in cache_hits
            and cache_hits[CLASSIFIER_VERSION_KEY] == DocumentClassifier.FORMAT_VERSION
            and cache_hits[CLASSIFIER_VERSION_KEY] == doc_suggestions.classifier_version
        ) and (
            CLASSIFIER_HASH_KEY in cache_hits
            and cache_hits[CLASSIFIER_HASH_KEY] == doc_suggestions.classifier_hash
        ):
            return doc_suggestions
        else:  # pragma: no cover
            # Remove the key because something didn't match
            cache.delete(doc_key)
    return None


def set_suggestions_cache(
    document_id: int,
    suggestions: dict,
    classifier: Optional["DocumentClassifier"],
    *,
    timeout=CACHE_50_MINUTES,
) -> None:
    """
    Caches the given suggestions, which were generated by the given classifier.  If there is no classifier,
    this function is a no-op (there won't be suggestions then anyway)
    """
    if classifier is not None:
        doc_key = get_suggestion_cache_key(document_id)
        cache.set(
            doc_key,
            SuggestionCacheData(
                classifier.FORMAT_VERSION,
                hexlify(classifier.last_auto_type_hash).decode(),
                suggestions,
            ),
            timeout,
        )


def refresh_suggestions_cache(
    document_id: int,
    *,
    timeout: int = CACHE_50_MINUTES,
) -> None:
    """
    Refreshes the expiration of the suggestions for the given document ID
    to the given timeout
    """
    doc_key = get_suggestion_cache_key(document_id)
    cache.touch(doc_key, timeout)


def get_metadata_cache_key(document_id: int) -> str:
    """
    Returns the basic key for a document's metadata
    """
    return f"doc_{document_id}_metadata"


def get_metadata_cache(document_id: int) -> Optional[MetadataCacheData]:
    """
    Returns the cached document metadata for the given document ID, as long as the metadata
    was cached once and the checksums have not changed
    """
    doc_key = get_metadata_cache_key(document_id)
    doc_metadata: Optional[MetadataCacheData] = cache.get(doc_key)
    # The metadata exists in the cache
    if doc_metadata is not None:
        try:
            doc = Document.objects.get(pk=document_id)
            # The original checksums match
            # If it has one, the archive checksums match
            # Then, we can use the metadata
            if (
                doc_metadata.original_checksum == doc.checksum
                and doc.has_archive_version
                and doc_metadata.archive_checksum is not None
                and doc_metadata.archive_checksum == doc.archive_checksum
            ):
                # Refresh cache
                cache.touch(doc_key, CACHE_50_MINUTES)
                return doc_metadata
            else:  # pragma: no cover
                # Something didn't match, delete the key
                cache.delete(doc_key)
        except Document.DoesNotExist:  # pragma: no cover
            # Basically impossible, but the key existed, but the Document didn't
            cache.delete(doc_key)
    return None


def set_metadata_cache(
    document: Document,
    original_metadata: list,
    archive_metadata: Optional[list],
    *,
    timeout=CACHE_50_MINUTES,
) -> None:
    """
    Sets the metadata into cache for the given Document
    """
    doc_key = get_metadata_cache_key(document.pk)
    cache.set(
        doc_key,
        MetadataCacheData(
            document.checksum,
            original_metadata,
            document.archive_checksum,
            archive_metadata,
        ),
        timeout,
    )


def refresh_metadata_cache(
    document_id: int,
    *,
    timeout: int = CACHE_50_MINUTES,
) -> None:
    """
    Refreshes the expiration of the metadata for the given document ID
    to the given timeout
    """
    doc_key = get_metadata_cache_key(document_id)
    cache.touch(doc_key, timeout)


def clear_metadata_cache(document_id: int) -> None:
    doc_key = get_metadata_cache_key(document_id)
    cache.delete(doc_key)


def get_thumbnail_modified_key(document_id: int) -> str:
    """
    Builds the key to store a thumbnail's timestamp
    """
    return f"doc_{document_id}_thumbnail_modified"
