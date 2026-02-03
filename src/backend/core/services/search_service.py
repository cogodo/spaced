import os
import re
from pathlib import Path
from typing import List, Optional

import httpx

from core.models import SearchResult
from core.monitoring.logger import get_logger
from infrastructure.storage import get_document_storage

logger = get_logger("search_service")

# MorphLLM API configuration
MORPH_API_URL = "https://api.morphllm.com/v1/chat/completions"
MORPH_WARP_GREP_MODEL = "morph-warp-grep-v1"


class SearchService:
    """
    Service for searching user documents.

    Uses keyword-based grep search which is fast and effective for document content.

    Note: WarpGrep integration is available but requires a tool-call loop for
    proper multi-step search. For document content search, grep-based search
    is more appropriate and efficient.
    """

    def __init__(self):
        self.storage = get_document_storage()
        self.morph_api_key = os.getenv("MORPH_API_KEY")
        # WarpGrep requires tool-call loop; use grep-based search by default
        # Set USE_WARPGREP=true to enable experimental WarpGrep support
        self.use_warpgrep = os.getenv("USE_WARPGREP", "").lower() == "true" and bool(self.morph_api_key)

        if self.use_warpgrep:
            logger.info("WarpGrep enabled for document search (experimental)")
        else:
            logger.info("Using grep-based search for documents")

    async def search_documents(
        self,
        query: str,
        user_id: str,
        topic_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Search user's documents for relevant content.

        Args:
            query: Natural language search query
            user_id: User's ID
            topic_id: Optional topic ID to limit search scope
            document_ids: Optional list of specific document IDs to search
            limit: Maximum number of results to return

        Returns:
            List of SearchResult with matching content
        """
        # Determine search paths
        search_paths = await self._get_search_paths(user_id, topic_id, document_ids)

        if not search_paths:
            logger.info(f"No documents to search for user {user_id}")
            return []

        if self.use_warpgrep:
            try:
                return await self._search_with_warpgrep(query, search_paths, limit)
            except Exception as e:
                logger.warning(f"WarpGrep search failed, falling back to grep: {e}")
                return await self._search_with_grep(query, search_paths, limit)
        else:
            return await self._search_with_grep(query, search_paths, limit)

    async def _get_search_paths(
        self,
        user_id: str,
        topic_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Path]:
        """Get the paths to search based on filters"""
        if document_ids:
            # Search specific documents
            paths = []
            for doc_id in document_ids:
                path = self.storage.get_document_path(user_id, doc_id)
                if path.exists():
                    paths.append(path)
            return paths

        if topic_id:
            # Search documents linked to a topic
            # We need to query the repository for this
            from core.repositories import DocumentRepository

            repo = DocumentRepository()
            documents = repo.list_by_topic(user_id, topic_id)
            return [
                self.storage.get_document_path(user_id, doc.id)
                for doc in documents
                if self.storage.get_document_path(user_id, doc.id).exists()
            ]

        # Search all user documents
        user_path = self.storage.get_user_documents_path(user_id)
        if user_path.exists():
            return [user_path]
        return []

    async def _search_with_grep(self, query: str, search_paths: List[Path], limit: int) -> List[SearchResult]:
        """
        Simple grep-based search over content files.

        Uses ripgrep (rg) if available, falls back to grep.
        """
        results = []

        # Extract keywords from query for searching
        keywords = self._extract_keywords(query)

        for path in search_paths:
            # Search for content.md files
            if path.is_dir():
                content_files = list(path.rglob("content.md"))
            else:
                content_files = [path / "content.md"] if (path / "content.md").exists() else []

            for content_file in content_files:
                matches = self._grep_file(content_file, keywords)
                for match in matches:
                    doc_id = self._extract_doc_id(content_file)
                    results.append(
                        SearchResult(
                            file=str(content_file),
                            content=match,
                            documentId=doc_id,
                        )
                    )

                    if len(results) >= limit:
                        return results

        return results[:limit]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract searchable keywords from natural language query"""
        # Remove common stop words
        stop_words = {
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "and",
            "but",
            "if",
            "or",
            "because",
            "until",
            "while",
            "about",
            "find",
            "search",
            "look",
            "get",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "am",
            "it",
            "its",
            "information",
            "relevant",
        }

        # Tokenize and filter
        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords if keywords else words[:5]

    def _grep_file(self, file_path: Path, keywords: List[str]) -> List[str]:
        """Search a file for keywords and return matching sections"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return []

        matches = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if any keyword matches
            if any(kw in line_lower for kw in keywords):
                # Get context: 2 lines before and after
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])

                # Avoid duplicate contexts
                if context not in matches:
                    matches.append(context)

        return matches

    def _extract_doc_id(self, file_path: Path) -> str:
        """Extract document ID from file path"""
        # Path structure: .../user_id/doc_id/content.md
        parts = file_path.parts
        for i, part in enumerate(parts):
            if part.startswith("doc_"):
                return part
        # Fallback: use parent directory name
        return file_path.parent.name

    async def _search_with_warpgrep(self, query: str, search_paths: List[Path], limit: int) -> List[SearchResult]:
        """
        Search using MorphLLM WarpGrep agentic search.

        WarpGrep uses AI to intelligently search through files
        with multiple tool calls.
        """
        results = []

        for search_path in search_paths:
            # Get directory structure for WarpGrep
            repo_structure = self._get_directory_tree(search_path, max_depth=3)

            # Build the search request
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a code search agent. Search through the provided "
                        "directory structure to find content relevant to the user's query. "
                        "Use the available tools to explore and read files."
                    ),
                },
                {
                    "role": "user",
                    "content": f"<repo_structure>{repo_structure}</repo_structure>\n<search_string>{query}</search_string>",
                },
            ]

            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        MORPH_API_URL,
                        headers={
                            "Authorization": f"Bearer {self.morph_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": MORPH_WARP_GREP_MODEL,
                            "messages": messages,
                            "temperature": 0.0,
                            "max_tokens": 4096,
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        warp_results = self._parse_warpgrep_response(data, search_path)
                        results.extend(warp_results)
                    else:
                        logger.warning(f"WarpGrep API error: {response.status_code} - {response.text}")

            except Exception as e:
                logger.error(f"WarpGrep request failed: {e}")
                raise

        return results[:limit]

    def _get_directory_tree(self, path: Path, max_depth: int = 3) -> str:
        """Generate a directory tree for WarpGrep"""
        lines = []

        def walk(current_path: Path, depth: int, prefix: str = ""):
            if depth > max_depth:
                return

            try:
                items = sorted(current_path.iterdir())
            except PermissionError:
                return

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item.name}")

                if item.is_dir() and depth < max_depth:
                    extension = "    " if is_last else "│   "
                    walk(item, depth + 1, prefix + extension)

        lines.append(str(path.name))
        walk(path, 1)

        return "\n".join(lines)

    def _parse_warpgrep_response(self, response: dict, base_path: Path) -> List[SearchResult]:
        """Parse WarpGrep response and extract search results"""
        results = []

        try:
            choices = response.get("choices", [])
            if not choices:
                return results

            content = choices[0].get("message", {}).get("content", "")

            # WarpGrep returns results with file paths and content
            # Parse the structured output
            # Format varies but typically includes file references

            # Simple extraction: look for file references and content
            file_pattern = r"(?:File|file|Path|path):\s*([^\n]+)"
            content_pattern = r"(?:Content|content|Snippet|snippet):\s*(.+?)(?=(?:File|file|Path|path):|$)"

            file_matches = re.findall(file_pattern, content)
            content_matches = re.findall(content_pattern, content, re.DOTALL)

            for i, file_path in enumerate(file_matches):
                file_content = content_matches[i] if i < len(content_matches) else ""
                doc_id = self._extract_doc_id(Path(file_path))

                results.append(
                    SearchResult(
                        file=file_path.strip(),
                        content=file_content.strip(),
                        documentId=doc_id,
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to parse WarpGrep response: {e}")

        return results

    async def search_for_context(
        self,
        query: str,
        user_id: str,
        topic_id: str,
        max_results: int = 5,
    ) -> str:
        """
        Get relevant context from documents for a question.

        Returns formatted context string for use in LLM prompts.
        """
        results = await self.search_documents(
            query=f"Information relevant to: {query}",
            user_id=user_id,
            topic_id=topic_id,
            limit=max_results,
        )

        if not results:
            return ""

        context_parts = []
        for r in results:
            # Clean up file path for display
            display_path = Path(r.file).name
            context_parts.append(f"From {display_path}:\n{r.content}")

        return "\n\n---\n\n".join(context_parts)
