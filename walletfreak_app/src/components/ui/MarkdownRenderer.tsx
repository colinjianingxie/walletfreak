import React from 'react';
import { View, Text, StyleSheet, Linking, ScrollView } from 'react-native';

interface MarkdownRendererProps {
  children: string;
}

interface InlineSegment {
  text: string;
  bold?: boolean;
  italic?: boolean;
  link?: string;
  code?: boolean;
}

/**
 * Lightweight markdown renderer for React Native.
 * Supports: headings, bold, italic, inline code, links, blockquotes,
 * unordered/ordered lists, horizontal rules, and paragraphs.
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ children }) => {
  const lines = (children || '').split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Blank line → skip
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Horizontal rule
    if (/^(-{3,}|_{3,}|\*{3,})\s*$/.test(line.trim())) {
      elements.push(<View key={i} style={styles.hr} />);
      i++;
      continue;
    }

    // Headings
    const headingMatch = line.match(/^(#{1,6})\s+(.+)/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const content = headingMatch[2];
      const headingStyle = level === 1 ? styles.h1 : level === 2 ? styles.h2 : styles.h3;
      elements.push(
        <Text key={i} style={headingStyle}>
          {renderInline(content)}
        </Text>
      );
      i++;
      continue;
    }

    // Blockquote (collect consecutive > lines)
    if (line.trimStart().startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trimStart().startsWith('>')) {
        quoteLines.push(lines[i].replace(/^\s*>\s?/, ''));
        i++;
      }
      elements.push(
        <View key={`bq-${i}`} style={styles.blockquote}>
          <Text style={styles.blockquoteText}>
            {renderInline(quoteLines.join(' '))}
          </Text>
        </View>
      );
      continue;
    }

    // Unordered list (collect consecutive - or * items)
    const ulMatch = line.match(/^\s*[-*+]\s+(.*)/);
    if (ulMatch) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*+]\s+(.*)/.test(lines[i])) {
        const m = lines[i].match(/^\s*[-*+]\s+(.*)/);
        if (m) items.push(m[1]);
        i++;
      }
      elements.push(
        <View key={`ul-${i}`} style={styles.list}>
          {items.map((item, idx) => (
            <View key={idx} style={styles.listItem}>
              <Text style={styles.bullet}>{'\u2022'}</Text>
              <Text style={styles.listText}>{renderInline(item)}</Text>
            </View>
          ))}
        </View>
      );
      continue;
    }

    // Ordered list
    const olMatch = line.match(/^\s*(\d+)[.)]\s+(.*)/);
    if (olMatch) {
      const items: string[] = [];
      let num = parseInt(olMatch[1], 10);
      while (i < lines.length && /^\s*\d+[.)]\s+(.*)/.test(lines[i])) {
        const m = lines[i].match(/^\s*\d+[.)]\s+(.*)/);
        if (m) items.push(m[1]);
        i++;
      }
      elements.push(
        <View key={`ol-${i}`} style={styles.list}>
          {items.map((item, idx) => (
            <View key={idx} style={styles.listItem}>
              <Text style={styles.bullet}>{num + idx}.</Text>
              <Text style={styles.listText}>{renderInline(item)}</Text>
            </View>
          ))}
        </View>
      );
      continue;
    }

    // Code block (``` fenced)
    if (line.trimStart().startsWith('```')) {
      const codeLines: string[] = [];
      i++; // skip opening fence
      while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing fence
      elements.push(
        <View key={`code-${i}`} style={styles.codeBlock}>
          <Text style={styles.codeBlockText}>{codeLines.join('\n')}</Text>
        </View>
      );
      continue;
    }

    // Table (lines starting with |)
    if (line.trim().startsWith('|')) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      if (tableLines.length >= 2) {
        const parseRow = (row: string): string[] =>
          row.split('|').slice(1, -1).map((c) => c.trim());

        const headerCells = parseRow(tableLines[0]);
        // Skip separator row (index 1 which is |---|---|)
        const startIdx = tableLines.length > 1 && /^[\s|:-]+$/.test(tableLines[1]) ? 2 : 1;
        const dataRows = tableLines.slice(startIdx).map(parseRow);

        elements.push(
          <ScrollView key={`table-${i}`} horizontal showsHorizontalScrollIndicator={true} style={styles.tableScroll}>
            <View>
              {/* Header row */}
              <View style={styles.tableRow}>
                {headerCells.map((cell, ci) => (
                  <View key={ci} style={[styles.tableHeaderCell]}>
                    <Text style={styles.tableHeaderText}>{cell}</Text>
                  </View>
                ))}
              </View>
              {/* Data rows */}
              {dataRows.map((row, ri) => (
                <View key={ri} style={[styles.tableRow, ri % 2 === 1 && styles.tableRowAlt]}>
                  {row.map((cell, ci) => (
                    <View key={ci} style={styles.tableCell}>
                      <Text style={styles.tableCellText}>{cell}</Text>
                    </View>
                  ))}
                </View>
              ))}
            </View>
          </ScrollView>
        );
        continue;
      }
    }

    // Paragraph — collect consecutive non-special lines
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].match(/^#{1,6}\s/) &&
      !lines[i].trimStart().startsWith('>') &&
      !lines[i].match(/^\s*[-*+]\s+/) &&
      !lines[i].match(/^\s*\d+[.)]\s+/) &&
      !lines[i].trimStart().startsWith('```') &&
      !lines[i].trim().startsWith('|') &&
      !/^(-{3,}|_{3,}|\*{3,})\s*$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      elements.push(
        <Text key={`p-${i}`} style={styles.paragraph}>
          {renderInline(paraLines.join(' '))}
        </Text>
      );
    }
  }

  return <View>{elements}</View>;
};

/**
 * Parse inline markdown: **bold**, *italic*, `code`, [text](url)
 */
function renderInline(text: string): React.ReactNode[] {
  const segments: InlineSegment[] = [];
  // Regex: bold, italic, inline code, links
  const regex = /(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`(.+?)`)|(\[([^\]]+)\]\(([^)]+)\))/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    // Plain text before this match
    if (match.index > lastIndex) {
      segments.push({ text: text.slice(lastIndex, match.index) });
    }

    if (match[1]) {
      // **bold**
      segments.push({ text: match[2], bold: true });
    } else if (match[3]) {
      // *italic*
      segments.push({ text: match[4], italic: true });
    } else if (match[5]) {
      // `code`
      segments.push({ text: match[6], code: true });
    } else if (match[7]) {
      // [text](url)
      segments.push({ text: match[8], link: match[9] });
    }

    lastIndex = match.index + match[0].length;
  }

  // Remaining plain text
  if (lastIndex < text.length) {
    segments.push({ text: text.slice(lastIndex) });
  }

  return segments.map((seg, idx) => {
    if (seg.link) {
      return (
        <Text
          key={idx}
          style={styles.link}
          onPress={() => Linking.openURL(seg.link!)}
        >
          {seg.text}
        </Text>
      );
    }
    if (seg.code) {
      return (
        <Text key={idx} style={styles.inlineCode}>{seg.text}</Text>
      );
    }
    const style = [
      seg.bold && styles.bold,
      seg.italic && styles.italic,
    ].filter(Boolean);
    if (style.length > 0) {
      return <Text key={idx} style={style}>{seg.text}</Text>;
    }
    return <React.Fragment key={idx}>{seg.text}</React.Fragment>;
  });
}

const styles = StyleSheet.create({
  // Headings
  h1: {
    fontSize: 24,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginTop: 24,
    marginBottom: 12,
  },
  h2: {
    fontSize: 20,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginTop: 20,
    marginBottom: 10,
  },
  h3: {
    fontSize: 18,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    marginTop: 16,
    marginBottom: 8,
  },
  // Paragraph
  paragraph: {
    fontSize: 16,
    fontFamily: 'Outfit',
    lineHeight: 26,
    color: '#1C1B1F',
    marginBottom: 12,
  },
  // Inline styles
  bold: {
    fontFamily: 'Outfit-Bold',
  },
  italic: {
    fontStyle: 'italic',
  },
  link: {
    color: '#4361EE',
    textDecorationLine: 'underline',
  },
  inlineCode: {
    fontFamily: 'monospace',
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 4,
    fontSize: 14,
    borderRadius: 3,
  },
  // Blockquote
  blockquote: {
    borderLeftWidth: 3,
    borderLeftColor: '#4361EE',
    paddingLeft: 16,
    paddingVertical: 8,
    backgroundColor: '#F5F3FF',
    borderRadius: 4,
    marginVertical: 12,
  },
  blockquoteText: {
    fontSize: 15,
    fontFamily: 'Outfit',
    fontStyle: 'italic',
    color: '#374151',
    lineHeight: 24,
  },
  // Lists
  list: {
    marginBottom: 12,
  },
  listItem: {
    flexDirection: 'row',
    marginBottom: 4,
    paddingLeft: 4,
  },
  bullet: {
    fontSize: 16,
    fontFamily: 'Outfit',
    color: '#1C1B1F',
    width: 20,
    lineHeight: 26,
  },
  listText: {
    flex: 1,
    fontSize: 16,
    fontFamily: 'Outfit',
    color: '#1C1B1F',
    lineHeight: 26,
  },
  // Code block
  codeBlock: {
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 16,
    marginVertical: 12,
  },
  codeBlockText: {
    fontFamily: 'monospace',
    color: '#E2E8F0',
    fontSize: 13,
    lineHeight: 20,
  },
  // Horizontal rule
  hr: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 16,
  },
  // Table
  tableScroll: {
    marginVertical: 12,
  },
  tableRow: {
    flexDirection: 'row',
  },
  tableRowAlt: {
    backgroundColor: '#F8FAFC',
  },
  tableHeaderCell: {
    minWidth: 100,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#F1F5F9',
    borderBottomWidth: 2,
    borderBottomColor: '#CBD5E1',
    borderRightWidth: 1,
    borderRightColor: '#E2E8F0',
  },
  tableHeaderText: {
    fontSize: 14,
    fontFamily: 'Outfit-SemiBold',
    color: '#334155',
  },
  tableCell: {
    minWidth: 100,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    borderRightWidth: 1,
    borderRightColor: '#E2E8F0',
  },
  tableCellText: {
    fontSize: 14,
    fontFamily: 'Outfit',
    color: '#1C1B1F',
    lineHeight: 20,
  },
});
