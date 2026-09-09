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
        final_chunks
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

        let sep_len = separator.chars().count();
        let sep_cost = if self.keep_separator == KeepSeparator::False {
            sep_len
        } else {
            0
        };
        let split_lens: Vec<usize> = splits.iter().map(|s| s.chars().count()).collect();

        let mut start = 0;
        let mut total_len = 0;

        for end in 0..splits.len() {
            let split_len = split_lens[end];
            let count_in_doc = end - start;
            let added_len = split_len + if count_in_doc > 0 { sep_cost } else { 0 };

            if total_len + added_len > self.chunk_size && count_in_doc > 0 {
                if let Some(joined) = self._join_docs(&splits[start..end], separator) {
                    final_chunks.push(joined);
                }

                while start < end {
                    let overlap_len = total_len;
                    let new_total_len = overlap_len + split_len + sep_cost;

                    if overlap_len > self.chunk_overlap
                        || (new_total_len > self.chunk_size && overlap_len > 0)
                    {
                        let front_len = split_lens[start];
                        let rem_count = end - start;
                        total_len -= front_len + if rem_count > 1 { sep_cost } else { 0 };
                        start += 1;
                    } else {
                        break;
                    }
                }
            }

            let new_count = end - start;
            total_len += split_len + if new_count > 0 { sep_cost } else { 0 };
        }

        if start < splits.len() {
            if let Some(joined) = self._join_docs(&splits[start..splits.len()], separator) {
                final_chunks.push(joined);
            }
        }

        final_chunks
    }

    fn _join_docs(&self, docs: &[String], separator: &str) -> Option<String> {
        let text = if self.keep_separator == KeepSeparator::False {
            docs.join(separator)
        } else {
            docs.join("")
        };

        let final_text = if self.strip_whitespace {
            text.trim().to_string()
        } else {
            text.clone()
        };

        #[allow(clippy::if_same_then_else)]
        if self.strip_whitespace && final_text.is_empty() && !text.is_empty() {
            None
        } else if final_text.is_empty() && text.is_empty() {
            None
        } else {
            Some(final_text)
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
