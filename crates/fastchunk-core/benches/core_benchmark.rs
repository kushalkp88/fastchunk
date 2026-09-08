use criterion::{black_box, criterion_group, criterion_main, Criterion};
use fastchunk_core::RecursiveCharacterTextSplitter;

fn generate_text(size_kb: usize, kind: &str) -> String {
    let chars = size_kb * 1024;
    let block = match kind {
        "plain" => "This is a simple plain English paragraph used for benchmarking text splitters. It contains average sized words and typical punctuation. ".repeat(5) + "\n\n",
        "markdown" => "## Markdown Heading\n\nHere is a paragraph with some **bold** text and `inline code`.\n\n```python\ndef foo():\n    return 'bar'\n```\n\n".to_string(),
        "source_code" => "def recursive_function(n):\n    if n <= 1:\n        return n\n    return recursive_function(n-1) + recursive_function(n-2)\n\n".to_string(),
        "unicode" => "これはテスト文書です。ベンチマークの目的で使用されます。テキストを正しく分割できるか確認します。\n\n".to_string(),
        "emoji" => "Hello world! 👨‍👩‍👧‍👦 This is a test 🚀 with multi-byte emojis! 🍕🍔\n\n".to_string(),
        _ => panic!("Unknown kind"),
    };

    let repetitions = (chars / block.chars().count()) + 1;
    let full = block.repeat(repetitions);
    full.chars().take(chars).collect()
}

fn bench_splitters(c: &mut Criterion) {
    let data_10kb_plain = generate_text(10, "plain");
    let data_10kb_markdown = generate_text(10, "markdown");
    let data_10kb_source = generate_text(10, "source_code");
    let data_10kb_unicode = generate_text(10, "unicode");
    let data_10kb_emoji = generate_text(10, "emoji");

    let data_1kb_plain = generate_text(1, "plain");
    let data_1mb_plain = generate_text(1000, "plain");
    let data_100kb_unicode = generate_text(100, "unicode");

    let data_100kb_plain = generate_text(100, "plain");


    // Conf A: 1000/200
    let splitter_a = RecursiveCharacterTextSplitter::new().with_chunk_size(1000).with_chunk_overlap(200);

    c.bench_function("fastchunk_core_10kb_plain_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_10kb_plain))));
    c.bench_function("fastchunk_core_10kb_markdown_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_10kb_markdown))));
    c.bench_function("fastchunk_core_10kb_source_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_10kb_source))));
    c.bench_function("fastchunk_core_10kb_unicode_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_10kb_unicode))));
    c.bench_function("fastchunk_core_10kb_emoji_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_10kb_emoji))));
    c.bench_function("fastchunk_core_100kb_plain_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_100kb_plain))));

    c.bench_function("fastchunk_core_1kb_plain_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_1kb_plain))));
    c.bench_function("fastchunk_core_1mb_plain_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_1mb_plain))));
    c.bench_function("fastchunk_core_100kb_unicode_1000_200", |b| b.iter(|| splitter_a.split_text(black_box(&data_100kb_unicode))));


    // Conf B: 500/50
    let splitter_b = RecursiveCharacterTextSplitter::new().with_chunk_size(500).with_chunk_overlap(50);
    c.bench_function("fastchunk_core_10kb_plain_500_50", |b| b.iter(|| splitter_b.split_text(black_box(&data_10kb_plain))));

    // Conf C: 2000/200
    let splitter_c = RecursiveCharacterTextSplitter::new().with_chunk_size(2000).with_chunk_overlap(200);
    c.bench_function("fastchunk_core_10kb_plain_2000_200", |b| b.iter(|| splitter_c.split_text(black_box(&data_10kb_plain))));
}

criterion_group!(benches, bench_splitters);
criterion_main!(benches);
