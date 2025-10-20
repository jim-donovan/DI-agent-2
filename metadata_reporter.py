"""
Metadata Reporter
Generates reports on AI metadata cleaning across document processing
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from collections import Counter


@dataclass
class MetadataCleaningReport:
    """Report of AI metadata cleaned from a document."""
    total_pages_processed: int
    pages_with_cleaned_metadata: int
    total_fragments_removed: int
    fragments_by_type: Dict[str, int]
    fragments_by_page: Dict[int, List[str]]
    cleaning_rate: float  # Percentage of pages that had metadata removed

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# AI Metadata Cleaning Report",
            "",
            "## Summary",
            f"- **Total Pages Processed**: {self.total_pages_processed}",
            f"- **Pages with Cleaned Metadata**: {self.pages_with_cleaned_metadata}",
            f"- **Total Fragments Removed**: {self.total_fragments_removed}",
            f"- **Cleaning Rate**: {self.cleaning_rate:.1f}%",
            "",
        ]

        if self.total_fragments_removed > 0:
            lines.extend([
                "## Fragments Removed by Type",
                "",
            ])
            for fragment_type, count in sorted(self.fragments_by_type.items(),
                                              key=lambda x: x[1], reverse=True):
                lines.append(f"- **{fragment_type}**: {count}")

            lines.extend([
                "",
                "## Details by Page",
                "",
            ])

            for page_num in sorted(self.fragments_by_page.keys()):
                fragments = self.fragments_by_page[page_num]
                lines.append(f"### Page {page_num} ({len(fragments)} fragment{'' if len(fragments) == 1 else 's'})")
                for fragment in fragments:
                    lines.append(f"- {fragment}")
                lines.append("")
        else:
            lines.extend([
                "## Result",
                "",
                "✅ No AI metadata detected - all responses were clean!",
                ""
            ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_pages_processed": self.total_pages_processed,
            "pages_with_cleaned_metadata": self.pages_with_cleaned_metadata,
            "total_fragments_removed": self.total_fragments_removed,
            "fragments_by_type": self.fragments_by_type,
            "fragments_by_page": {str(k): v for k, v in self.fragments_by_page.items()},
            "cleaning_rate": self.cleaning_rate
        }


class MetadataReporter:
    """Aggregates and reports on AI metadata cleaning."""

    @staticmethod
    def generate_report(agent_responses: List[Any], total_pages: int = None) -> MetadataCleaningReport:
        """Generate cleaning report from agent responses.

        Args:
            agent_responses: List of AgentResponse objects from processing
            total_pages: Actual number of pages processed (if None, uses len(agent_responses))

        Returns:
            MetadataCleaningReport with aggregated statistics
        """
        if total_pages is None:
            total_pages = len(agent_responses)
        fragments_by_page = {}
        all_fragments = []

        for response in agent_responses:
            # Get page number from metadata
            page_num = response.metadata.get("page_number", 0)

            # Get removed metadata
            removed = response.metadata.get("removed_metadata", [])

            if removed:
                fragments_by_page[page_num] = removed
                all_fragments.extend(removed)

        # Count fragment types
        fragment_types = Counter()
        for fragment in all_fragments:
            # Extract type from "Type: 'text'" format
            if ":" in fragment:
                fragment_type = fragment.split(":", 1)[0].strip()
                fragment_types[fragment_type] += 1

        # Calculate statistics
        pages_with_cleaned = len(fragments_by_page)
        total_fragments = len(all_fragments)
        cleaning_rate = (pages_with_cleaned / total_pages * 100) if total_pages > 0 else 0.0

        return MetadataCleaningReport(
            total_pages_processed=total_pages,
            pages_with_cleaned_metadata=pages_with_cleaned,
            total_fragments_removed=total_fragments,
            fragments_by_type=dict(fragment_types),
            fragments_by_page=fragments_by_page,
            cleaning_rate=cleaning_rate
        )

    @staticmethod
    def generate_summary(agent_responses: List[Any]) -> str:
        """Generate a quick summary string.

        Args:
            agent_responses: List of AgentResponse objects

        Returns:
            Short summary string
        """
        report = MetadataReporter.generate_report(agent_responses)

        if report.total_fragments_removed == 0:
            return "✅ No AI metadata detected"

        return (f"🧹 Cleaned {report.total_fragments_removed} metadata fragment(s) "
                f"from {report.pages_with_cleaned_metadata}/{report.total_pages_processed} pages "
                f"({report.cleaning_rate:.1f}%)")

    @staticmethod
    def log_cleaning_stats(agent_responses: List[Any], logger=None) -> None:
        """Log cleaning statistics.

        Args:
            agent_responses: List of AgentResponse objects
            logger: Optional ProcessingLogger instance
        """
        report = MetadataReporter.generate_report(agent_responses)

        if logger:
            if report.total_fragments_removed > 0:
                logger.log_step(
                    f"AI Metadata Cleaning: {report.total_fragments_removed} fragments removed "
                    f"from {report.pages_with_cleaned_metadata} pages"
                )

                # Log top fragment types
                top_types = sorted(report.fragments_by_type.items(),
                                 key=lambda x: x[1], reverse=True)[:3]
                if top_types:
                    types_str = ", ".join([f"{t}: {c}" for t, c in top_types])
                    logger.log_step(f"Most common: {types_str}")
            else:
                logger.log_success("No AI metadata detected - clean responses!")
