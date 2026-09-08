use regex::Regex;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KeepSeparator {
    True,
    False,
    Start,
    End,
}

pub struct RecursiveCharacterTextSplitter {
    separators: Vec<String>,
    chunk_size: usize,
    chunk_overlap: usize,
    keep_separator: KeepSeparator,
    is_separator_regex: bool,
    strip_whitespace: bool,
}

impl Default for RecursiveCharacterTextSplitter {
    fn default() -> Self {
        Self {
            separators: vec![
                "\n\n".to_string(),
                "\n".to_string(),
                " ".to_string(),
                "".to_string(),
            ],
            chunk_size: 4000,
            chunk_overlap: 200,
            keep_separator: KeepSeparator::True,
            is_separator_regex: false,
            strip_whitespace: true,
        }
    }
}

impl RecursiveCharacterTextSplitter {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_separators(mut self, separators: Vec<String>) -> Self {
        self.separators = separators;
        self
    }

    pub fn with_chunk_size(mut self, chunk_size: usize) -> Self {
        self.chunk_size = chunk_size;
        self
    }

    pub fn with_chunk_overlap(mut self, chunk_overlap: usize) -> Self {
        self.chunk_overlap = chunk_overlap;
        self
    }

    pub fn with_keep_separator(mut self, keep_separator: KeepSeparator) -> Self {
        self.keep_separator = keep_separator;
        self
    }

    pub fn with_is_separator_regex(mut self, is_separator_regex: bool) -> Self {
        self.is_separator_regex = is_separator_regex;
        self
    }

    pub fn with_strip_whitespace(mut self, strip_whitespace: bool) -> Self {
        self.strip_whitespace = strip_whitespace;
        self
    }

    pub fn split_text(&self, text: &str) -> Vec<String> {
        let mut final_chunks: Vec<String> = Vec::new();
        let separators: Vec<&str> = self.separators.iter().map(|s| s.as_str()).collect();
        self._split_text(text, &separators, &mut final_chunks);

        if self.strip_whitespace {
            final_chunks
                .into_iter()
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .collect()
        } else {
            final_chunks
        }
    }

    fn _split_text(&self, text: &str, separators: &[&str], final_chunks: &mut Vec<String>) {
        if text.is_empty() {
            return;
        }

        let mut separator = if separators.is_empty() {
            ""
        } else {
            separators.last().unwrap()
        };
        let mut new_separators = &[] as &[&str];

        for (i, &s) in separators.iter().enumerate() {
            if s.is_empty() {
                separator = s;
                break;
            }
            let found = if self.is_separator_regex {
                if let Ok(re) = Regex::new(s) {
                    re.is_match(text)
                } else {
                    false
                }
            } else {
                text.find(s).is_some()
            };

            if found {
                separator = s;
                new_separators = &separators[i + 1..];
                break;
            }
        }

        let splits = self._split_text_with_separator(text, separator);

        let mut good_splits = Vec::new();
        let sep_for_merge = match self.keep_separator {
            KeepSeparator::False => separator,
            _ => "",
        };

        for split in splits {
            let split_len = split.chars().count();
            if split_len < self.chunk_size {
                good_splits.push(split.to_string());
            } else {
                if !good_splits.is_empty() {
                    let mut merged = self._merge_splits(&good_splits, sep_for_merge);
                    final_chunks.append(&mut merged);
                    good_splits.clear();
                }

                if new_separators.is_empty() {
                    final_chunks.push(split.to_string());
                } else {
                    self._split_text(split, new_separators, final_chunks);
                }
            }
        }

        if !good_splits.is_empty() {
            let mut merged = self._merge_splits(&good_splits, sep_for_merge);
            final_chunks.append(&mut merged);
        }
    }

    fn _split_text_with_separator<'a>(&self, text: &'a str, separator: &str) -> Vec<&'a str> {
        let mut result = Vec::new();

        if separator.is_empty() {
            for (idx, _) in text.char_indices() {
                let end = text[idx..].chars().next().unwrap().len_utf8() + idx;
                result.push(&text[idx..end]);
            }
            return result;
        }

        if self.is_separator_regex {
            if let Ok(re) = Regex::new(separator) {
                let mut last_end = 0;
                for m in re.find_iter(text) {
                    let start = m.start();
                    let end = m.end();

                    match self.keep_separator {
                        KeepSeparator::False => {
                            if start > last_end {
                                result.push(&text[last_end..start]);
                            }
                        }
                        KeepSeparator::End => {
                            result.push(&text[last_end..end]);
                        }
                        KeepSeparator::Start | KeepSeparator::True => {
                            if start > last_end {
                                result.push(&text[last_end..start]);
                            }
                            last_end = start;
                            continue;
                        }
                    }
                    last_end = end;
                }

                if last_end < text.len() {
                    result.push(&text[last_end..]);
                }
            } else {
                result.push(text);
            }
        } else {
            let mut last_end = 0;
            let sep_len = separator.len();
            for (start, _) in text.match_indices(separator) {
                match self.keep_separator {
                    KeepSeparator::False => {
                        result.push(&text[last_end..start]);
                    }
                    KeepSeparator::End => {
                        result.push(&text[last_end..start + sep_len]);
                    }
                    KeepSeparator::Start | KeepSeparator::True => {
                        if start > last_end {
                            result.push(&text[last_end..start]);
                        }
                        last_end = start;
                        continue;
                    }
                }
                last_end = start + sep_len;
            }
            if last_end < text.len() {
                result.push(&text[last_end..]);
            }
        }

        if self.keep_separator == KeepSeparator::False {
            result.retain(|s| !s.is_empty());
        }

        result
    }

    fn _merge_splits(&self, splits: &[String], separator: &str) -> Vec<String> {
        let mut final_chunks = Vec::new();
        if splits.is_empty() {
            return final_chunks;
        }

        let mut current_chunks: Vec<String> = Vec::new();
        let sep_len = separator.chars().count();

        for split in splits {
            let split_len = split.chars().count();

            let mut current_docs_len = 0;
            for (i, c) in current_chunks.iter().enumerate() {
                current_docs_len += c.chars().count();
                if i > 0 && self.keep_separator == KeepSeparator::False {
                    current_docs_len += sep_len;
                }
            }

            let total_len = if current_chunks.is_empty() {
                split_len
            } else {
                current_docs_len
                    + split_len
                    + if self.keep_separator == KeepSeparator::False {
                        sep_len
                    } else {
                        0
                    }
            };

            if total_len > self.chunk_size && !current_chunks.is_empty() {
                let joined = self._join_docs(&current_chunks, separator);
                final_chunks.push(joined);

                while !current_chunks.is_empty() {
                    let mut overlap_len = 0;
                    for (i, c) in current_chunks.iter().enumerate() {
                        overlap_len += c.chars().count();
                        if i > 0 && self.keep_separator == KeepSeparator::False {
                            overlap_len += sep_len;
                        }
                    }

                    let new_total_len = if current_chunks.is_empty() {
                        split_len
                    } else {
                        overlap_len
                            + split_len
                            + if self.keep_separator == KeepSeparator::False {
                                sep_len
                            } else {
                                0
                            }
                    };

                    if overlap_len > self.chunk_overlap
                        || (new_total_len > self.chunk_size && overlap_len > 0)
                    {
                        current_chunks.remove(0);
                    } else {
                        break;
                    }
                }
            }

            current_chunks.push(split.clone());
        }

        if !current_chunks.is_empty() {
            let joined = self._join_docs(&current_chunks, separator);
            final_chunks.push(joined);
        }

        final_chunks
    }

    fn _join_docs(&self, docs: &[String], separator: &str) -> String {
        if self.keep_separator == KeepSeparator::False {
            docs.join(separator)
        } else {
            docs.join("")
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_text() {
        let splitter = RecursiveCharacterTextSplitter::new().with_chunk_size(10);
        let chunks = splitter.split_text("");
        assert!(chunks.is_empty());
    }

    #[test]
    fn test_text_shorter_than_chunk_size() {
        let text = "Hello world";
        let splitter = RecursiveCharacterTextSplitter::new().with_chunk_size(50);
        let chunks = splitter.split_text(text);
        assert_eq!(chunks, vec!["Hello world"]);
    }

    #[test]
    fn test_exact_chunk_size_boundaries() {
        let text = "a b c d e f";
        let splitter = RecursiveCharacterTextSplitter::new()
            .with_chunk_size(3)
            .with_chunk_overlap(0)
            .with_strip_whitespace(false)
            .with_keep_separator(KeepSeparator::False);
        let chunks = splitter.split_text(text);
        assert_eq!(chunks, vec!["a b", "c d", "e f"]);
    }

    #[test]
    fn test_exact_chunk_size_boundaries_keep_separator() {
        let text = "a b c d e f";
        let splitter = RecursiveCharacterTextSplitter::new()
            .with_chunk_size(3)
            .with_chunk_overlap(0)
            .with_strip_whitespace(false)
            .with_keep_separator(KeepSeparator::True);
        let chunks = splitter.split_text(text);
        assert_eq!(chunks, vec!["a b", " c", " d", " e", " f"]);
    }

    #[test]
    fn test_multiple_paragraphs() {
        let text = "Para 1\n\nPara 2\n\nPara 3";
        let splitter = RecursiveCharacterTextSplitter::new()
            .with_chunk_size(10)
            .with_chunk_overlap(0);
        let chunks = splitter.split_text(text);
        assert_eq!(chunks, vec!["Para 1", "Para 2", "Para 3"]);
    }

    #[test]
    fn test_fallback_to_character_splitting() {
        let text = "abcdefghij";
        let splitter = RecursiveCharacterTextSplitter::new()
            .with_chunk_size(3)
            .with_chunk_overlap(0);
        let chunks = splitter.split_text(text);
        assert_eq!(chunks, vec!["abc", "def", "ghi", "j"]);
    }

    #[test]
    fn test_unicode_text() {
        let text = "こんにちは世界";
        let splitter = RecursiveCharacterTextSplitter::new()
            .with_chunk_size(3)
            .with_chunk_overlap(0);
        let chunks = splitter.split_text(text);
        assert_eq!(chunks, vec!["こんに", "ちは世", "界"]);
    }
}
