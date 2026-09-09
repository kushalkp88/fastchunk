use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
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
    let sizes = [1, 10, 100, 1000];
    let kinds = ["plain", "markdown", "source_code", "unicode", "emoji"];
    let configs = [(1000, 200), (500, 50), (2000, 200)];

    let mut group = c.benchmark_group("fastchunk_core");

    // To keep benchmark times reasonable, we reduce sample sizes for large texts.
    group.sample_size(10);

    for &size in &sizes {
        for &kind in &kinds {
            let text = generate_text(size, kind);
            for &(chunk_size, chunk_overlap) in &configs {
                let id = format!("{}kb_{}_{}_{}", size, kind, chunk_size, chunk_overlap);
                let splitter = RecursiveCharacterTextSplitter::new()
                    .with_chunk_size(chunk_size)
                    .with_chunk_overlap(chunk_overlap);
                group.bench_with_input(BenchmarkId::from_parameter(&id), &text, |b, t| {
                    b.iter(|| splitter.split_text(black_box(t)));
                });
            }
        }
    }
    group.finish();
}

criterion_group!(benches, bench_splitters);
criterion_main!(benches);
