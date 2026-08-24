from app.graph.images import inject_images, unwrap_outer_markdown_fence
from app.graph.nodes.image_gen import editorial_prompt
from app.graph.state import ImageAsset, ImageStatus


def test_injects_hero_and_caption_after_title():
    images = [
        ImageAsset(
            image_id="img_1",
            prompt="hero",
            caption="Cover illustration. AI-generated.",
            url="/api/pipeline/r/images/img_1.png",
            status=ImageStatus.GENERATED,
        ),
        ImageAsset(
            image_id="img_2",
            prompt="diagram",
            caption="Visual explainer. AI-generated.",
            url="/api/pipeline/r/images/img_2.png",
            status=ImageStatus.GENERATED,
        ),
    ]
    md = "# Title\n\nIntro\n\n## One\n\nA\n\n## Two\n\nB\n"
    out = inject_images(md, images)
    assert "](/api/pipeline/r/images/img_1.png)" in out
    assert "*Cover illustration. AI-generated.*" in out
    assert out.index("img_1.png") < out.index("## One")
    assert "](/api/pipeline/r/images/img_2.png)" in out
    assert inject_images(out, images) == out


def test_unwraps_outer_markdown_fence():
    wrapped = "```markdown\n# Title\n\nHello\n\n```python\nprint(1)\n```\n\nBye\n```"
    out = unwrap_outer_markdown_fence(wrapped)
    assert out.startswith("# Title")
    assert not out.startswith("```")
    assert out.endswith("Bye")
    assert "```python" in out


def test_replace_refreshes_captions():
    images = [
        ImageAsset(
            image_id="img_1",
            prompt="hero",
            caption="New caption. AI-generated.",
            url="/api/pipeline/r/images/img_1.png",
            status=ImageStatus.GENERATED,
        )
    ]
    md = "# Title\n\n![Old caption](/api/pipeline/r/images/img_1.png)\n\n*Old caption*\n\nHello\n"
    out = inject_images(md, images, replace=True)
    assert "New caption. AI-generated." in out
    assert "Old caption" not in out


def test_strips_example_dot_com_placeholders():
    images = [
        ImageAsset(
            image_id="img_1",
            prompt="hero",
            caption="Caption here. AI-generated.",
            url="/api/pipeline/r/images/img_1.png",
            status=ImageStatus.GENERATED,
        )
    ]
    md = "# Title\n\n![Fake](https://example.com/bpe-diagram)\n\n*Fake*\n\nHello\n"
    out = inject_images(md, images)
    assert "example.com" not in out
    assert "/api/pipeline/r/images/img_1.png" in out


def test_editorial_prompt_rejects_abstract_plan_copy():
    prompt = editorial_prompt(
        "How Byte Pair Encoding Works",
        "BPE merges frequent character pairs",
        planned="An abstract illustration of tokenization in natural language processing",
        cover=False,
    )
    assert "abstract illustration" not in prompt.lower()
    assert "BPE merges frequent character pairs" in prompt
    assert "No letters" in prompt


def test_editorial_prompt_keeps_a_concrete_plan():
    planned = "Tiles merging into larger tiles to show BPE pair merges, no text"
    prompt = editorial_prompt("How BPE works", "BPE merges pairs", planned=planned)
    assert "Tiles merging" in prompt
