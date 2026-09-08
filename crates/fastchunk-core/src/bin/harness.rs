use fastchunk_core::{KeepSeparator, RecursiveCharacterTextSplitter};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 7 {
        eprintln!("Usage: test text chunk_size overlap keep_sep strip_ws");
        return;
    }

    let text = &args[1];
    let chunk_size: usize = args[2].parse().unwrap();
    let chunk_overlap: usize = args[3].parse().unwrap();
    let keep_sep = match args[4].as_str() {
        "true" => KeepSeparator::True,
        "false" => KeepSeparator::False,
        "start" => KeepSeparator::Start,
        "end" => KeepSeparator::End,
        _ => KeepSeparator::True,
    };
    let strip_ws: bool = args[5].parse().unwrap();
    let separators_arg = &args[6];

    let separators: Vec<String> = if separators_arg == "default" {
        vec![
            "\n\n".to_string(),
            "\n".to_string(),
            " ".to_string(),
            "".to_string(),
        ]
    } else {
        serde_json::from_str(separators_arg).unwrap()
    };

    let splitter = RecursiveCharacterTextSplitter::new()
        .with_chunk_size(chunk_size)
        .with_chunk_overlap(chunk_overlap)
        .with_keep_separator(keep_sep)
        .with_strip_whitespace(strip_ws)
        .with_separators(separators);

    let chunks = splitter.split_text(text);
    println!("{}", serde_json::to_string(&chunks).unwrap());
}
