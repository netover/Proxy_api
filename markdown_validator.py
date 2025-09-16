#!/usr/bin/env python3
"""
Markdown Validator and Converter - Intelligent Edition

Script avançado para validar e corrigir arquivos Markdown com análise inteligente
de padrões e correções otimizadas para garantir qualidade da documentação.

🚀 Funcionalidades Inteligentes:
    • Análise abrangente de todos os problemas de uma vez
    • Identificação de padrões recorrentes
    • Correções em lote otimizadas
    • Estratégia de correção baseada em severidade
    • Relatórios detalhados com insights

📋 Validações Suportadas:
    • MD022: Headers devem ter linhas em branco ao redor
    • MD024: Headers duplicados
    • MD031: Blocos de código devem ter linhas em branco ao redor
    • MD032: Listas devem ter linhas em branco ao redor
    • MD034: URLs devem estar formatadas como links
    • MD036: Ênfase não deve ser usada como cabeçalho
    • MD040: Blocos de código devem especificar linguagem
    • MD042: Links não devem ter texto ou URL vazios
    • MD047: Arquivos devem terminar com newline
    • MD051: Fragmentos de link devem ser válidos

Uso:
    python markdown_validator.py --validate docs/          # Valida arquivos
    python markdown_validator.py --analyze docs/           # Análise de padrões
    python markdown_validator.py --fix docs/               # Correções individuais
    python markdown_validator.py --bulk-fix docs/          # Correções em lote inteligentes
    python markdown_validator.py --report docs/            # Relatório detalhado
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Representa um problema encontrado na validação"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggestion: str = ""
    can_fix: bool = False


@dataclass
class ValidationResult:
    """Resultado da validação de um arquivo"""

    file_path: str
    is_valid: bool
    issues: List[ValidationIssue]
    total_lines: int
    fixed_issues: int = 0


class MarkdownValidator:
    """Validador e corretor de arquivos Markdown"""

    def __init__(self):
        self.issues_found = []

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Valida um arquivo Markdown com análise inteligente de problemas"""
        logger.debug(f"Validating {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path} as UTF-8")
            return ValidationResult(str(file_path), False, [], 0)

        lines = content.split("\n")

        # Análise inteligente: executa todas as validações em paralelo conceitual
        # e identifica padrões para correções otimizadas
        all_issues = self._comprehensive_analysis(
            content, lines, str(file_path)
        )

        # Otimiza issues removendo duplicatas e agrupando similares
        optimized_issues = self._optimize_issues(all_issues)

        is_valid = len(optimized_issues) == 0
        return ValidationResult(
            str(file_path), is_valid, optimized_issues, len(lines)
        )

    def _comprehensive_analysis(
        self, content: str, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Análise abrangente que identifica todos os problemas de uma vez"""
        issues = []

        # Análise estrutural completa
        structural_issues = self._analyze_structure(content, lines, file_path)
        issues.extend(structural_issues)

        # Análise de conteúdo
        content_issues = self._analyze_content(content, lines, file_path)
        issues.extend(content_issues)

        # Análise de formatação
        formatting_issues = self._analyze_formatting(content, lines, file_path)
        issues.extend(formatting_issues)

        return issues

    def _analyze_structure(
        self, content: str, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Analisa estrutura do documento (headers, listas, blocos)"""
        issues = []

        # Headers (MD022, MD024)
        issues.extend(self._validate_headers(lines, file_path))
        issues.extend(self._validate_duplicate_headings(content, file_path))

        # Listas (MD032)
        issues.extend(self._validate_lists(lines, file_path))

        # Blocos de código (MD031, MD040)
        issues.extend(self._validate_code_blocks(content, file_path))

        # Tabelas
        issues.extend(self._validate_tables(content, file_path))

        return issues

    def _analyze_content(
        self, content: str, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Analisa conteúdo (links, URLs, ênfase)"""
        issues = []

        # Links (MD042, MD051)
        issues.extend(self._validate_links(content, file_path))
        issues.extend(self._validate_link_fragments(content, file_path))

        # URLs sem formatação (MD034)
        issues.extend(self._validate_bare_urls(content, file_path))

        # Ênfase como cabeçalho (MD036)
        issues.extend(self._validate_emphasis_as_heading(content, file_path))

        return issues

    def _analyze_formatting(
        self, content: str, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Analisa formatação geral"""
        issues = []

        # Linhas em branco consecutivas (MD012)
        issues.extend(self._validate_blank_lines(lines, file_path))

        # Newline no final (MD047)
        issues.extend(self._validate_trailing_newline(content, file_path))

        return issues

    def _optimize_issues(
        self, issues: List[ValidationIssue]
    ) -> List[ValidationIssue]:
        """Otimiza lista de issues removendo duplicatas e agrupando similares"""
        if not issues:
            return issues

        # Remove duplicatas exatas
        seen = set()
        unique_issues = []
        for issue in issues:
            key = (
                issue.file_path,
                issue.line_number,
                issue.issue_type,
                issue.message,
            )
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        # Agrupa issues similares na mesma linha
        grouped_issues = []
        line_groups = {}

        for issue in unique_issues:
            key = (issue.file_path, issue.line_number)
            if key not in line_groups:
                line_groups[key] = []
            line_groups[key].append(issue)

        # Para linhas com múltiplos issues, prioriza os mais críticos
        for (file_path, line_num), line_issues in line_groups.items():
            if len(line_issues) == 1:
                grouped_issues.extend(line_issues)
            else:
                # Ordena por severidade e mantém apenas os mais importantes
                sorted_issues = sorted(
                    line_issues,
                    key=lambda x: self._get_severity_priority(x.severity),
                )
                # Mantém no máximo 3 issues por linha para evitar spam
                grouped_issues.extend(sorted_issues[:3])

        return grouped_issues

    def _get_severity_priority(self, severity: str) -> int:
        """Retorna prioridade para ordenação (menor número = maior prioridade)"""
        priorities = {"error": 0, "warning": 1, "info": 2}
        return priorities.get(severity, 3)

    def _validate_headers(
        self, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Valida headers Markdown"""
        issues = []

        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                # Verifica espaço após hashtags
                if not re.match(r"^#{1,6}\s", line):
                    issues.append(
                        ValidationIssue(
                            file_path,
                            i,
                            "header_format",
                            "warning",
                            "Header should have space after #",
                            "Add space after #",
                            True,
                        )
                    )

                # Verifica linhas em branco ao redor (MD022)
                # Verifica linha anterior
                if i > 1:
                    prev_line = lines[
                        i - 2
                    ]  # i-2 porque enumerate começa em 1
                    if prev_line.strip() and not prev_line.startswith("#"):
                        issues.append(
                            ValidationIssue(
                                file_path,
                                i,
                                "header_spacing_above",
                                "info",
                                "Header should be surrounded by blank lines [Expected: 1; Actual: 0; Above]",
                                "Add blank line before header",
                                True,
                            )
                        )

                # Verifica linha seguinte
                if i < len(lines):
                    next_line = lines[i]  # Próxima linha
                    if next_line.strip() and not next_line.startswith("#"):
                        issues.append(
                            ValidationIssue(
                                file_path,
                                i,
                                "header_spacing_below",
                                "info",
                                "Header should be surrounded by blank lines [Expected: 1; Actual: 0; Below]",
                                "Add blank line after header",
                                True,
                            )
                        )

        return issues

    def _validate_code_blocks(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida blocos de código (MD031, MD040)"""
        issues = []

        lines = content.split("\n")

        # Encontra blocos de código
        code_block_pattern = r"```(\w+)?\n(.*?)\n```"
        matches = re.finditer(code_block_pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1)
            start_pos = content[: match.start()].count("\n") + 1
            end_pos = content[: match.end()].count("\n") + 1

            # MD040: Code block should specify language
            if not language:
                issues.append(
                    ValidationIssue(
                        file_path,
                        start_pos,
                        "code_block_language",
                        "warning",
                        "Code block should specify language",
                        "Add language specifier (e.g., ```python)",
                        True,
                    )
                )

            # MD031: Blanks around fences
            # Verifica linha antes do bloco
            if start_pos > 1:
                prev_line = lines[
                    start_pos - 2
                ]  # -2 porque start_pos começa em 1
                if prev_line.strip():
                    issues.append(
                        ValidationIssue(
                            file_path,
                            start_pos,
                            "code_block_spacing_before",
                            "info",
                            "Fenced code blocks should be surrounded by blank lines",
                            "Add blank line before code block",
                            True,
                        )
                    )

            # Verifica linha depois do bloco
            if end_pos < len(lines):
                next_line = lines[end_pos]
                if next_line.strip():
                    issues.append(
                        ValidationIssue(
                            file_path,
                            end_pos,
                            "code_block_spacing_after",
                            "info",
                            "Fenced code blocks should be surrounded by blank lines",
                            "Add blank line after code block",
                            True,
                        )
                    )

        # Verifica blocos não fechados
        open_blocks = content.count("```")
        if open_blocks % 2 != 0:
            issues.append(
                ValidationIssue(
                    file_path,
                    1,
                    "code_block_unclosed",
                    "error",
                    "Unclosed code block found",
                    "Ensure all code blocks are properly closed",
                    True,
                )
            )

        return issues

    def _validate_links(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida links Markdown"""
        issues = []

        # Padrão para links: [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.finditer(link_pattern, content)

        for match in matches:
            text, url = match.group(1), match.group(2)

            # Verifica URLs vazias
            if not url.strip():
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ValidationIssue(
                        file_path,
                        line_num,
                        "link_empty_url",
                        "error",
                        f"Link '{text}' has empty URL",
                        "Provide valid URL",
                        True,
                    )
                )

            # Verifica texto vazio
            if not text.strip():
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ValidationIssue(
                        file_path,
                        line_num,
                        "link_empty_text",
                        "warning",
                        "Link has empty text",
                        "Provide descriptive link text",
                        True,
                    )
                )

        return issues

    def _validate_lists(
        self, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Valida listas Markdown (MD032)"""
        issues = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Verifica se é uma linha de lista
            if stripped.startswith(("- ", "* ", "+ ")) or re.match(
                r"^\d+\.\s", stripped
            ):
                # Verifica linha anterior (deve ter linha em branco antes)
                if i > 1:
                    prev_line = lines[
                        i - 2
                    ]  # i-2 porque enumerate começa em 1
                    if (
                        prev_line.strip()
                        and not prev_line.startswith(("#", "-", "*", "+"))
                        and not re.match(r"^\d+\.\s", prev_line.strip())
                    ):
                        issues.append(
                            ValidationIssue(
                                file_path,
                                i,
                                "list_spacing",
                                "info",
                                "Lists should be surrounded by blank lines",
                                "Add blank line before list",
                                True,
                            )
                        )

                # Verifica linha seguinte (deve ter linha em branco depois)
                if i < len(lines):
                    next_line = lines[i]
                    if (
                        next_line.strip()
                        and not next_line.startswith(("#", "-", "*", "+"))
                        and not re.match(r"^\d+\.\s", next_line.strip())
                    ):
                        issues.append(
                            ValidationIssue(
                                file_path,
                                i,
                                "list_spacing_after",
                                "info",
                                "Lists should be surrounded by blank lines",
                                "Add blank line after list",
                                True,
                            )
                        )

        return issues

    def _validate_tables(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida tabelas Markdown"""
        issues = []

        lines = content.split("\n")
        in_table = False
        header_separator_found = False

        for i, line in enumerate(lines, 1):
            if "|" in line and not line.strip().startswith("|"):
                if not in_table:
                    in_table = True
                    header_separator_found = False
                elif not header_separator_found:
                    # Verifica linha separadora
                    if not re.match(r"^\s*\|[\s\-\|:]+\|\s*$", line):
                        issues.append(
                            ValidationIssue(
                                file_path,
                                i,
                                "table_separator",
                                "error",
                                "Invalid table separator line",
                                "Use |---|---| format for table separator",
                                True,
                            )
                        )
                    header_separator_found = True
            elif line.strip() and in_table:
                # Sai da tabela
                in_table = False
                header_separator_found = False

        return issues

    def _validate_link_fragments(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida fragmentos de link (MD051)"""
        issues = []

        # Padrão para links com fragmentos: [text](url#fragment)
        link_fragment_pattern = r"\[([^\]]+)\]\(([^)]*#[^)]+)\)"
        matches = re.finditer(link_fragment_pattern, content)

        for match in matches:
            url = match.group(2)
            if "#" in url:
                fragment = url.split("#", 1)[1]
                # Verifica se o fragmento contém caracteres especiais (acentos, etc.)
                normalized_fragment = self._normalize_fragment(fragment)
                if fragment != normalized_fragment:
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        ValidationIssue(
                            file_path,
                            line_num,
                            "link_fragments",
                            "warning",
                            f"Link fragment '{fragment}' should use ASCII characters",
                            f"Replace with '{normalized_fragment}'",
                            True,
                        )
                    )

        return issues

    def _normalize_fragment(self, fragment: str) -> str:
        """Normaliza fragmento removendo acentos e caracteres especiais"""
        # Remove acentos e converte para ASCII
        import unicodedata

        normalized = (
            unicodedata.normalize("NFD", fragment)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        # Substitui espaços e caracteres especiais por hífens
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized)
        # Remove hífens duplicados e leading/trailing
        return re.sub(r"-+", "-", normalized).strip("-").lower()

    def _validate_blank_lines(
        self, lines: List[str], file_path: str
    ) -> List[ValidationIssue]:
        """Valida linhas em branco consecutivas (MD012)"""
        issues = []

        consecutive_blanks = 0
        for i, line in enumerate(lines, 1):
            if not line.strip():
                consecutive_blanks += 1
                if consecutive_blanks > 1:
                    issues.append(
                        ValidationIssue(
                            file_path,
                            i,
                            "multiple_blanks",
                            "info",
                            f"Multiple consecutive blank lines [Expected: 1; Actual: {consecutive_blanks}]",
                            "Remove extra blank lines",
                            True,
                        )
                    )
            else:
                consecutive_blanks = 0

        return issues

    def _validate_bare_urls(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida URLs sem formatação (MD034)"""
        issues = []

        # Padrão para URLs sem formatação Markdown
        # Evita URLs dentro de links já formatados
        url_pattern = r'(?<!\]\()https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.finditer(url_pattern, content)

        for match in matches:
            url = match.group(0)
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                ValidationIssue(
                    file_path,
                    line_num,
                    "bare_urls",
                    "warning",
                    f"Bare URL used: {url[:50]}...",
                    "Format URL as [text](url)",
                    True,
                )
            )

        return issues

    def _validate_emphasis_as_heading(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida ênfase usada como cabeçalho (MD036)"""
        issues = []

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Verifica se a linha tem ênfase forte (* ou _) e não é cabeçalho
            if (
                stripped.count("**") >= 2 or stripped.count("__") >= 2
            ) and not stripped.startswith("#"):
                # Verifica se parece ser um cabeçalho (maiúsculas, curto)
                if len(stripped) < 100 and any(
                    word[0].isupper() for word in stripped.split() if word
                ):
                    issues.append(
                        ValidationIssue(
                            file_path,
                            i,
                            "emphasis_as_heading",
                            "warning",
                            "Emphasis used instead of a heading",
                            "Use # for heading instead of emphasis",
                            False,
                        )
                    )

        return issues

    def _validate_trailing_newline(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida newline no final do arquivo (MD047)"""
        issues = []

        if not content.endswith("\n"):
            issues.append(
                ValidationIssue(
                    file_path,
                    len(content.split("\n")),
                    "trailing_newline",
                    "info",
                    "Files should end with a single newline character",
                    "Add newline at end of file",
                    True,
                )
            )
        elif content.endswith("\n\n"):
            issues.append(
                ValidationIssue(
                    file_path,
                    len(content.split("\n")),
                    "trailing_newline",
                    "info",
                    "Files should end with a single newline character",
                    "Remove extra trailing newlines",
                    True,
                )
            )

        return issues

    def _validate_duplicate_headings(
        self, content: str, file_path: str
    ) -> List[ValidationIssue]:
        """Valida cabeçalhos duplicados (MD024)"""
        issues = []

        lines = content.split("\n")
        headings = {}

        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                # Extrai o texto do cabeçalho
                heading_text = line.lstrip("#").strip()
                if heading_text in headings:
                    issues.append(
                        ValidationIssue(
                            file_path,
                            i,
                            "duplicate_heading",
                            "warning",
                            f"Multiple headings with the same content: '{heading_text}'",
                            "Rename one of the headings to make them unique",
                            False,
                        )
                    )
                else:
                    headings[heading_text] = i

        return issues

    def fix_file(self, file_path: Path) -> int:
        """Corrige automaticamente problemas em um arquivo com abordagem inteligente"""
        logger.info(f"Fixing {file_path}")

        result = self.validate_file(file_path)
        if not result.issues:
            return 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.error(f"Could not read {file_path}")
            return 0

        original_content = content

        # Estratégia inteligente: agrupa correções por tipo para aplicar em lote
        fixes_applied = self._apply_intelligent_fixes(
            content, result.issues, file_path
        )

        # Salva se houve mudanças
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Applied {fixes_applied} fixes to {file_path}")

        return fixes_applied

    def _apply_intelligent_fixes(
        self, content: str, issues: List[ValidationIssue], file_path: str
    ) -> int:
        """Aplica correções de forma inteligente, agrupando por tipo"""
        fixes_applied = 0
        lines = content.split("\n")

        # Agrupa issues por tipo para correções em lote
        issues_by_type = {}
        for issue in issues:
            if issue.can_fix:
                if issue.issue_type not in issues_by_type:
                    issues_by_type[issue.issue_type] = []
                issues_by_type[issue.issue_type].append(issue)

        # Aplica correções por tipo (mais eficiente)
        for issue_type, type_issues in issues_by_type.items():
            if issue_type in ["header_spacing_above", "header_spacing_below"]:
                fixes_applied += self._fix_header_spacing_batch(
                    lines, type_issues
                )
            elif issue_type == "multiple_blanks":
                fixes_applied += self._fix_multiple_blanks_batch(
                    lines, type_issues
                )
            elif issue_type == "header_format":
                fixes_applied += self._fix_header_format_batch(
                    lines, type_issues
                )
            elif issue_type == "trailing_newline":
                fixes_applied += self._fix_trailing_newline(lines, type_issues)
            elif issue_type in [
                "code_block_spacing_before",
                "code_block_spacing_after",
            ]:
                fixes_applied += self._fix_code_block_spacing_batch(
                    content, lines, type_issues
                )
            elif issue_type == "code_block_language":
                fixes_applied += self._fix_code_block_language_batch(
                    lines, type_issues
                )
            elif issue_type == "link_fragments":
                fixes_applied += self._fix_link_fragments_batch(
                    lines, type_issues
                )
            elif (
                issue_type == "list_spacing"
                or issue_type == "list_spacing_after"
            ):
                fixes_applied += self._fix_list_spacing_batch(
                    lines, type_issues
                )
            elif issue_type == "bare_urls":
                fixes_applied += self._fix_bare_urls_batch(lines, type_issues)
            else:
                # Correções individuais para tipos não otimizados
                for issue in type_issues:
                    new_content = self._apply_fix("\n".join(lines), issue)
                    lines = new_content.split("\n")
                    fixes_applied += 1

        return fixes_applied

    def _fix_header_spacing_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige espaçamento de headers em lote"""
        fixes_applied = 0
        processed_lines = set()

        for issue in issues:
            line_idx = issue.line_number - 1  # Converte para índice 0-based

            if line_idx in processed_lines:
                continue

            if issue.issue_type == "header_spacing_above" and line_idx > 0:
                # Adiciona linha em branco antes
                if lines[
                    line_idx - 1
                ].strip():  # Só adiciona se não houver linha em branco
                    lines.insert(line_idx, "")
                    fixes_applied += 1
                    processed_lines.add(line_idx)

            elif (
                issue.issue_type == "header_spacing_below"
                and line_idx < len(lines) - 1
            ):
                # Adiciona linha em branco depois
                if lines[
                    line_idx + 1
                ].strip():  # Só adiciona se não houver linha em branco
                    lines.insert(line_idx + 1, "")
                    fixes_applied += 1
                    processed_lines.add(line_idx)

        return fixes_applied

    def _fix_multiple_blanks_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige múltiplas linhas em branco em lote"""
        if not lines:
            return 0

        # Remove todas as linhas em branco consecutivas, mantendo no máximo 1
        new_lines = []
        prev_blank = False

        for line in lines:
            if line.strip():
                new_lines.append(line)
                prev_blank = False
            elif not prev_blank:
                new_lines.append(line)
                prev_blank = True

        # Atualiza a lista original
        lines.clear()
        lines.extend(new_lines)

        return 1 if len(new_lines) != len(lines) else 0

    def _fix_header_format_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige formato de headers em lote"""
        fixes_applied = 0

        for issue in issues:
            line_idx = issue.line_number - 1
            if line_idx < len(lines):
                line = lines[line_idx]
                if line.startswith("#") and not line.startswith("# "):
                    lines[line_idx] = line.replace("#", "# ", 1)
                    fixes_applied += 1

        return fixes_applied

    def _fix_trailing_newline(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige newline no final do arquivo"""
        if not lines:
            return 0

        # Garante exatamente uma linha em branco no final
        while lines and not lines[-1].strip():
            lines.pop()

        if lines:
            lines.append("")  # Adiciona uma linha em branco no final

        return 1

    def _fix_code_block_spacing_batch(
        self, content: str, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige espaçamento de blocos de código em lote"""
        fixes_applied = 0

        # Encontra todos os blocos de código e suas posições
        code_blocks = []
        code_block_pattern = r"```(\w+)?\n(.*?)\n```"
        matches = re.finditer(code_block_pattern, content, re.DOTALL)

        for match in matches:
            start_pos = content[: match.start()].count("\n")
            end_pos = content[: match.end()].count("\n")

            # Verifica e adiciona espaçamento antes
            if start_pos > 0 and lines[start_pos - 1].strip():
                lines.insert(start_pos, "")
                fixes_applied += 1

            # Verifica e adiciona espaçamento depois (ajusta pelo insert anterior)
            if end_pos < len(lines) - 1 and lines[end_pos + 1].strip():
                lines.insert(end_pos + 1, "")
                fixes_applied += 1

        return fixes_applied

    def _fix_code_block_language_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige especificação de linguagem em blocos de código em lote"""
        fixes_applied = 0

        for issue in issues:
            line_idx = issue.line_number - 1
            if line_idx < len(lines) and lines[line_idx].strip() == "```":
                # Adiciona linguagem padrão como yaml se for código simples de configuração
                if line_idx + 2 < len(lines) and (
                    "api_keys:" in lines[line_idx + 2]
                    or "debug:" in lines[line_idx + 2]
                ):
                    lines[line_idx] = "```yaml"
                    fixes_applied += 1
                # Ou adiciona como bash se tiver comandos
                elif line_idx + 2 < len(lines) and any(
                    cmd in lines[line_idx + 2]
                    for cmd in ["python", "cd", "git", "npm"]
                ):
                    lines[line_idx] = "```bash"
                    fixes_applied += 1
                else:
                    # Linguagem genérica para código
                    lines[line_idx] = "```python"
                    fixes_applied += 1

        return fixes_applied

    def _fix_link_fragments_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige fragmentos de link em lote"""
        fixes_applied = 0

        for issue in issues:
            line_idx = issue.line_number - 1
            if line_idx < len(lines):
                line = lines[line_idx]
                # Procura por padrões de link com fragmentos
                link_pattern = r"\[(.*?)\]\([^)]*#([^)]+)\)"
                match = re.search(link_pattern, line)
                if match:
                    fragment = match.group(2)
                    normalized = self._normalize_fragment(fragment)
                    if fragment != normalized:
                        new_line = line.replace(
                            f"#{fragment}", f"#{normalized}"
                        )
                        if new_line != line:
                            lines[line_idx] = new_line
                            fixes_applied += 1

        return fixes_applied

    def _fix_list_spacing_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige espaçamento de listas em lote"""
        fixes_applied = 0
        processed_lines = set()

        for issue in issues:
            line_idx = issue.line_number - 1

            if line_idx in processed_lines or line_idx >= len(lines):
                continue

            if issue.issue_type == "list_spacing" and line_idx > 0:
                # Adiciona linha em branco antes da lista
                if lines[line_idx - 1].strip():
                    lines.insert(line_idx, "")
                    fixes_applied += 1
                    processed_lines.add(line_idx)

            elif (
                issue.issue_type == "list_spacing_after"
                and line_idx < len(lines) - 1
            ):
                # Adiciona linha em branco depois da lista
                if lines[line_idx + 1].strip():
                    lines.insert(line_idx + 1, "")
                    fixes_applied += 1
                    processed_lines.add(line_idx)

        return fixes_applied

    def _fix_bare_urls_batch(
        self, lines: List[str], issues: List[ValidationIssue]
    ) -> int:
        """Corrige URLs sem formatação em lote"""
        fixes_applied = 0

        for issue in issues:
            line_idx = issue.line_number - 1
            if line_idx < len(lines):
                line = lines[line_idx]
                # Procura URLs sem formatação
                url_pattern = r'(?<!\]\()(https?://[^\s<>"{}|\\^`\[\]]+)(?!\))'
                matches = re.finditer(url_pattern, line)

                for match in matches:
                    url = match.group(1)
                    # Cria um texto descritivo para o link baseado no URL
                    if "github.com" in url:
                        text = "GitHub"
                    elif "api.openai.com" in url:
                        text = "OpenAI API"
                    elif "anthropic.com" in url:
                        text = "Anthropic"
                    else:
                        text = (
                            url.split("/")[-1]
                            if "." in url.split("/")[-1]
                            else "Link"
                        )

                    # Substitui URL pela versão formatada
                    formatted_link = f"[{text}]({url})"
                    lines[line_idx] = line.replace(f"{url}", formatted_link)
                    fixes_applied += 1

        return fixes_applied

    def analyze_patterns(
        self, results: List[ValidationResult]
    ) -> Dict[str, Any]:
        """Analisa padrões nos resultados para identificar problemas recorrentes"""
        if not results:
            return {}

        patterns = {
            "most_common_issues": {},
            "files_with_most_issues": [],
            "severity_distribution": {"error": 0, "warning": 0, "info": 0},
            "fixable_vs_non_fixable": {"fixable": 0, "non_fixable": 0},
        }

        all_issues = []
        for result in results:
            all_issues.extend(result.issues)

        # Conta issues por tipo
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue.issue_type] = (
                issue_counts.get(issue.issue_type, 0) + 1
            )
            patterns["severity_distribution"][issue.severity] += 1

            if issue.can_fix:
                patterns["fixable_vs_non_fixable"]["fixable"] += 1
            else:
                patterns["fixable_vs_non_fixable"]["non_fixable"] += 1

        # Top 5 issues mais comuns
        patterns["most_common_issues"] = dict(
            sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        # Arquivos com mais issues
        file_issue_counts = []
        for result in results:
            if result.issues:
                file_issue_counts.append(
                    {
                        "file": result.file_path,
                        "issue_count": len(result.issues),
                        "fixable_count": sum(
                            1 for i in result.issues if i.can_fix
                        ),
                    }
                )

        patterns["files_with_most_issues"] = sorted(
            file_issue_counts, key=lambda x: x["issue_count"], reverse=True
        )[:5]

        return patterns

    def apply_bulk_fixes(
        self, results: List[ValidationResult], patterns: Dict[str, Any]
    ) -> int:
        """Aplica correções em lote baseadas em padrões identificados"""
        total_fixes = 0

        # Prioriza correção dos arquivos com mais issues
        for file_info in patterns.get("files_with_most_issues", []):
            file_path = Path(file_info["file"])
            if file_path.exists():
                fixes = self.fix_file(file_path)
                total_fixes += fixes
                logger.info(
                    f"Bulk fix: {file_path} - {fixes} corrections applied"
                )

        return total_fixes

    def _apply_fix(self, content: str, issue: ValidationIssue) -> str:
        """Aplica uma correção específica"""
        lines = content.split("\n")

        if issue.issue_type == "header_format":
            # Adiciona espaço após #
            line = lines[issue.line_number - 1]
            if line.startswith("#") and not line.startswith("# "):
                lines[issue.line_number - 1] = line.replace("#", "# ", 1)

        elif issue.issue_type == "header_spacing":
            # Adiciona linha em branco antes do header
            if issue.line_number > 1:
                lines.insert(issue.line_number - 1, "")

        elif issue.issue_type == "code_block_language":
            # Adiciona especificação de linguagem
            # Esta é uma correção mais complexa, vamos simplificar
            pass

        elif issue.issue_type == "link_empty_text":
            # Corrige texto vazio do link
            # Esta também é complexa, vamos simplificar
            pass

        elif issue.issue_type == "multiple_blanks":
            # Remove linhas em branco consecutivas
            new_lines = []
            prev_blank = False
            for line in lines:
                if line.strip():
                    new_lines.append(line)
                    prev_blank = False
                elif not prev_blank:
                    new_lines.append(line)
                    prev_blank = True
            lines = new_lines

        elif issue.issue_type == "bare_urls":
            # Converte URLs sem formatação para links Markdown
            # Esta é complexa, vamos simplificar por enquanto
            pass

        elif issue.issue_type == "trailing_newline":
            # Garante uma única linha em branco no final
            if lines and lines[-1].strip():
                lines.append("")
            elif (
                len(lines) > 1
                and not lines[-1].strip()
                and not lines[-2].strip()
            ):
                lines = lines[:-1]

        return "\n".join(lines)

    def generate_report(
        self, results: List[ValidationResult], output_format: str = "json"
    ) -> str:
        """Gera relatório de validação"""
        report = {
            "summary": {
                "total_files": len(results),
                "valid_files": sum(1 for r in results if r.is_valid),
                "invalid_files": sum(1 for r in results if not r.is_valid),
                "total_issues": sum(len(r.issues) for r in results),
                "total_fixable": sum(
                    sum(1 for i in r.issues if i.can_fix) for r in results
                ),
            },
            "files": [asdict(r) for r in results],
            "issues_by_type": self._group_issues_by_type(results),
        }

        if output_format == "json":
            return json.dumps(report, indent=2, ensure_ascii=False)
        elif output_format == "markdown":
            return self._generate_markdown_report(report)
        else:
            return json.dumps(report)

    def _group_issues_by_type(
        self, results: List[ValidationResult]
    ) -> Dict[str, int]:
        """Agrupa issues por tipo"""
        grouped = {}
        for result in results:
            for issue in result.issues:
                grouped[issue.issue_type] = (
                    grouped.get(issue.issue_type, 0) + 1
                )
        return grouped

    def _generate_markdown_report(self, report: Dict) -> str:
        """Gera relatório em formato Markdown"""
        md = ["# Markdown Validation Report\n"]

        # Summary
        summary = report["summary"]
        md.append("## Summary\n")
        md.append(f"- **Total Files**: {summary['total_files']}")
        md.append(f"- **Valid Files**: {summary['valid_files']}")
        md.append(f"- **Invalid Files**: {summary['invalid_files']}")
        md.append(f"- **Total Issues**: {summary['total_issues']}")
        md.append(f"- **Fixable Issues**: {summary['total_fixable']}")
        md.append("")

        # Issues by type
        if report["issues_by_type"]:
            md.append("## Issues by Type\n")
            for issue_type, count in report["issues_by_type"].items():
                md.append(f"- **{issue_type}**: {count}")
            md.append("")

        # File details
        md.append("## File Details\n")
        for file_info in report["files"]:
            status = "[OK]" if file_info["is_valid"] else "[ERROR]"
            md.append(f"### {status} {file_info['file_path']}")
            md.append(f"- **Lines**: {file_info['total_lines']}")
            md.append(f"- **Issues**: {len(file_info['issues'])}")

            if file_info["issues"]:
                md.append("**Issues Found:**")
                for issue in file_info["issues"]:
                    severity_icon = {
                        "error": "[ERROR]",
                        "warning": "[WARN]",
                        "info": "[INFO]",
                    }.get(issue["severity"], "[UNKNOWN]")
                    md.append(
                        f"- {severity_icon} Line {issue['line_number']}: {issue['message']}"
                    )

            md.append("")

        return "\n".join(md)


def find_markdown_files(directory: Path) -> List[Path]:
    """Encontra todos os arquivos Markdown em um diretório"""
    markdown_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".md", ".markdown")):
                markdown_files.append(Path(root) / file)
    return markdown_files


def main():
    parser = argparse.ArgumentParser(
        description="Markdown Validator and Converter"
    )
    parser.add_argument("path", help="Path to file or directory to validate")
    parser.add_argument(
        "--validate", action="store_true", help="Validate markdown files"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument(
        "--bulk-fix",
        action="store_true",
        help="Apply bulk fixes based on patterns",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate validation report"
    )
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Report format",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze patterns in validation results",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    path = Path(args.path)
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return 1

    # Encontra arquivos Markdown
    if path.is_file():
        markdown_files = [path]
    else:
        markdown_files = find_markdown_files(path)

    if not markdown_files:
        logger.warning("No markdown files found")
        return 0

    logger.info(f"Found {len(markdown_files)} markdown files")

    validator = MarkdownValidator()
    results = []

    # Estratégia inteligente: valida primeiro todos os arquivos para análise de padrões
    if args.validate or args.report or args.analyze or args.bulk_fix:
        logger.info(
            "[ANALYSIS] Phase 1: Validating all files for comprehensive analysis..."
        )
        for file_path in markdown_files:
            result = validator.validate_file(file_path)
            results.append(result)

            if args.validate:
                status = (
                    "[OK] Valid"
                    if result.is_valid
                    else f"[ERROR] {len(result.issues)} issues"
                )
                logger.info(f"{file_path}: {status}")

    # Análise de padrões se solicitada
    patterns = {}
    if args.analyze and results:
        logger.info(
            "[PATTERN] Phase 2: Analyzing patterns across all files..."
        )
        patterns = validator.analyze_patterns(results)

        print("\n" + "=" * 60)
        print("PATTERN ANALYSIS REPORT")
        print("=" * 60)

        if patterns.get("most_common_issues"):
            print("\n[*] Most Common Issues:")
            for issue_type, count in patterns["most_common_issues"].items():
                print(f"  - {issue_type}: {count} occurrences")

        if patterns.get("files_with_most_issues"):
            print("\n[*] Files with Most Issues:")
            for file_info in patterns["files_with_most_issues"][:3]:
                print(
                    f"  - {file_info['file']}: {file_info['issue_count']} issues ({file_info['fixable_count']} fixable)"
                )

        severity = patterns.get("severity_distribution", {})
        print(f"\n[*] Severity Distribution:")
        print(f"  - Errors: {severity.get('error', 0)}")
        print(f"  - Warnings: {severity.get('warning', 0)}")
        print(f"  - Info: {severity.get('info', 0)}")

        fixable = patterns.get("fixable_vs_non_fixable", {})
        print(f"\n[*] Fixable Issues: {fixable.get('fixable', 0)}")
        print(f"[*] Non-fixable Issues: {fixable.get('non_fixable', 0)}")

    # Correções em lote baseadas em padrões
    if args.bulk_fix and patterns:
        logger.info("[BULK] Phase 3: Applying bulk fixes based on patterns...")
        bulk_fixes = validator.apply_bulk_fixes(results, patterns)
        logger.info(
            f"[SUCCESS] Bulk fixes completed: {bulk_fixes} total corrections applied"
        )

    # Correções individuais se solicitadas
    elif args.fix:
        logger.info("[FIX] Phase 3: Applying individual fixes...")
        total_fixes = 0
        for file_path in markdown_files:
            fixes = validator.fix_file(file_path)
            if fixes > 0:
                logger.info(f"{file_path}: {fixes} fixes applied")
                total_fixes += fixes
        logger.info(
            f"[SUCCESS] Individual fixes completed: {total_fixes} total corrections applied"
        )

    # Gera relatório se solicitado
    if args.report and results:
        report = validator.generate_report(results, args.format)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Report saved to {args.output}")
        else:
            print(report)

    return 0


if __name__ == "__main__":
    exit(main())
