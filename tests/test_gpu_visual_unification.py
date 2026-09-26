"""
Regression tests for GPU scene visual unification.

Sources-of-truth: raw source text of scenes/sections.py GPU region
(lines 2160-2838). No manim rendering required.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_SECTIONS = ROOT / "scenes" / "sections.py"
_GPU_START = 2160  # line after "# 7900XTX GPU Benchmark Scenes — 11 scenes"
_GPU_END = 2838    # last line of SCENE_MAP before EOF


def _gpu_region() -> str:
    lines = _SECTIONS.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[_GPU_START - 1 : _GPU_END])


# ---------------------------------------------------------------------------
# Forbidden tokens inside the GPU region
# ---------------------------------------------------------------------------

class TestNoForbiddenColors:
    """GPU region must not reference semantic color config keys."""

    _FORBIDDEN = [
        "config.manim.success_color",
        "config.manim.warning_color",
        "config.manim.error_color",
        "config.chart_colors",
    ]

    def test_no_success_color_in_gpu_region(self):
        src = _gpu_region()
        hits = [(i + 1, line.rstrip())
                for i, line in enumerate(src.splitlines())
                if "config.manim.success_color" in line]
        if hits:
            pytest.fail(
                f"Found config.manim.success_color in GPU region at lines: "
                f"{[h[0] for h in hits]}\n" + "\n".join(f"  L{h[0]}: {h[1]}" for h in hits)
            )

    def test_no_warning_color_in_gpu_region(self):
        src = _gpu_region()
        hits = [(i + 1, line.rstrip())
                for i, line in enumerate(src.splitlines())
                if "config.manim.warning_color" in line]
        if hits:
            pytest.fail(
                f"Found config.manim.warning_color in GPU region at lines: "
                f"{[h[0] for h in hits]}\n" + "\n".join(f"  L{h[0]}: {h[1]}" for h in hits)
            )

    def test_no_error_color_in_gpu_region(self):
        src = _gpu_region()
        hits = [(i + 1, line.rstrip())
                for i, line in enumerate(src.splitlines())
                if "config.manim.error_color" in line]
        if hits:
            pytest.fail(
                f"Found config.manim.error_color in GPU region at lines: "
                f"{[h[0] for h in hits]}\n" + "\n".join(f"  L{h[0]}: {h[1]}" for h in hits)
            )

    def test_no_chart_colors_in_gpu_region(self):
        src = _gpu_region()
        hits = [(i + 1, line.rstrip())
                for i, line in enumerate(src.splitlines())
                if "config.chart_colors" in line]
        if hits:
            pytest.fail(
                f"Found config.chart_colors in GPU region at lines: "
                f"{[h[0] for h in hits]}\n" + "\n".join(f"  L{h[0]}: {h[1]}" for h in hits)
            )


# ---------------------------------------------------------------------------
# Zebra stripe coverage
# ---------------------------------------------------------------------------

class TestZebraStripeCoverage:
    """Every GPU table must use apply_zebra_stripes (not apply_row_colors)."""

    def test_at_least_six_zebra_calls(self):
        src = _gpu_region()
        count = src.count("apply_zebra_stripes")
        assert count >= 6, (
            f"Expected >= 6 apply_zebra_stripes calls in GPU region, found {count}"
        )

    def test_no_apply_row_colors_in_gpu_region(self):
        src = _gpu_region()
        hits = [(i + 1, line.rstrip())
                for i, line in enumerate(src.splitlines())
                if "apply_row_colors" in line]
        if hits:
            pytest.fail(
                f"Found apply_row_colors in GPU region at lines: "
                f"{[h[0] for h in hits]}\n" + "\n".join(f"  L{h[0]}: {h[1]}" for h in hits)
            )


# ---------------------------------------------------------------------------
# Official Sapphire image + caption
# ---------------------------------------------------------------------------

class TestOfficialGpuImage:
    def test_sapphire_image_path_present(self):
        src = _gpu_region()
        assert "sapphire_nitro_plus_white_7900xt_small.png" in src, (
            "GPUOpenScene must use sapphire_nitro_plus_white_7900xt_small.png"
        )

    def test_old_7900xtx_card_removed(self):
        src = _gpu_region()
        assert "7900xtx_card_small.png" not in src, (
            "Old 7900xtx_card_small.png must be removed from GPU region"
        )

    def test_appearance_caption_present(self):
        src = _gpu_region()
        assert "外观参考：蓝宝石 NITRO+ WHITE 7900 XT" in src, (
            "GPUOpenScene must include neutral appearance-reference caption"
        )


# ---------------------------------------------------------------------------
# GPUEnvScene terminal command count
# ---------------------------------------------------------------------------

class TestGPUEnvTerminalCommands:
    """GPUEnvScene must have at most 4 add_command calls."""

    def test_at_most_four_commands(self):
        src = _gpu_region()
        # Find GPUEnvScene region
        env_start = src.index("class GPUEnvScene")
        env_end = src.index("\nclass GPUSolutionsScene")
        env_src = src[env_start:env_end]
        count = env_src.count("term.add_command")
        assert count <= 4, (
            f"GPUEnvScene has {count} add_command calls, expected <= 4"
        )

    def test_no_success_color_in_gpuenv_terminal_lines(self):
        src = _gpu_region()
        env_start = src.index("class GPUEnvScene")
        env_end = src.index("\nclass GPUSolutionsScene")
        env_src = src[env_start:env_end]
        assert "config.manim.success_color" not in env_src, (
            "GPUEnvScene terminal lines must not use success_color"
        )


# ---------------------------------------------------------------------------
# Core benchmark data preserved
# ---------------------------------------------------------------------------

class TestCoreDataPreserved:
    """All key benchmark numbers and table content must remain."""

    _REQUIRED_STRINGS = [
        "DFlash",
        "Vulkan+MTP",
        "ROCm+MTP",
        "TurboQuant",
        "SGLang",
        "Qwen3.6",
        "Qwen3.8",
        "24GB",
        "ReBAR",
        "gfx1100",
        "64-86 t/s",
        "63-80 t/s",
        "46-54 t/s",
        "28-29 t/s",
        "38-80%",
        "TQ3_4S",
        "IQ4_XS",
        "UD-Q4_K_M",
        "Hybrid Gated DeltaNet",
        "262K",
        "128K",
        "Vulkan 编译失败",
        "运行时 OOM",
        "GTT 隐式溢出",
    ]

    def test_core_strings_present(self):
        src = _gpu_region()
        missing = [s for s in self._REQUIRED_STRINGS if s not in src]
        assert not missing, (
            f"Core benchmark strings missing from GPU region: {missing}"
        )


# ---------------------------------------------------------------------------
# Redundant bottom notes removed (most scenes)
# ---------------------------------------------------------------------------

class TestRedundantBottomNotesRemoved:
    """Scenes with table/card data should not repeat conclusions as separate text below."""

    def test_gpuhardware_no_redundant_tip(self):
        """GPUHardwareScene tip about ReBAR already in table; remove separate note."""
        src = _gpu_region()
        hw_start = src.index("class GPUHardwareScene")
        hw_end = src.index("\nclass GPUEnvScene")
        hw_src = src[hw_start:hw_end]
        # The old tip line used error_color and repeated ReBAR info
        assert "config.manim.error_color" not in hw_src, (
            "GPUHardwareScene should not use error_color"
        )

    def test_gpukuant_no_error_tip(self):
        src = _gpu_region()
        q_start = src.index("class GPUQuantScene")
        q_end = src.index("\nclass GPUVRAMScene")
        q_src = src[q_start:q_end]
        assert "config.manim.error_color" not in q_src, (
            "GPUQuantScene should not use error_color"
        )

    def test_gpuoutro_no_local_path(self):
        src = _gpu_region()
        out_start = src.index("class GPUOutroScene")
        # Must not contain local filesystem path
        assert "/Users/mac/scripts/" not in src[out_start:], (
            "GPUOutroScene must not reference local file path"
        )


# ---------------------------------------------------------------------------
# Card stroke uniformity in BIOS/Ranking/Backup
# ---------------------------------------------------------------------------

class TestGPUSpeedChartLabels:
    def test_both_charts_show_backend_names_and_headings(self):
        src = _gpu_region()
        start = src.index("class GPUSpeedScene")
        end = src.index("\nclass GPUArchScene")
        region = src[start:end]
        for token in ("names36", "names38", "sub36", "sub38"):
            assert token in region, f"GPUSpeedScene missing {token}"
        assert region.count("Write(names36)") == 1
        assert region.count("Write(names38)") == 1


class TestGPUSceneAnimationCompleteness:
    def test_open_scene_uses_staged_visual_blocks(self):
        src = _gpu_region()
        start = src.index("class GPUOpenScene")
        end = src.index("\nclass GPUHardwareScene")
        region = src[start:end]
        assert "FadeOut(gpu_img)" in region
        assert "FadeOut(caption)" in region
        assert "gpu_img.move_to(ORIGIN)" in region
        assert "FadeOut(VGroup(key_find_box, key_find))" in region

    def test_vram_scene_adds_model_headings(self):
        src = _gpu_region()
        start = src.index("class GPUVRAMScene")
        end = src.index("\nclass GPUBIOSScene")
        region = src[start:end]
        assert "Write(left_title)" in region
        assert "Write(right_title)" in region
        assert region.count("scale_to_fit_width(6.6)") == 2


class TestGPUOutroLayout:
    def test_outro_has_zhihu_article_and_no_bottom_edge_text(self):
        src = _gpu_region()
        start = src.index("class GPUOutroScene")
        region = src[start:]
        assert "https://zhuanlan.zhihu.com/p/2086731295925724100" in region
        assert 'Text("", font_size=12)' not in region
        assert ".to_edge(DOWN" not in region

    def test_outro_stacks_all_blocks_in_one_arrange_chain(self):
        region = _gpu_region()[_gpu_region().index("class GPUOutroScene"):]
        assert region.count("VGroup(") >= 3
        chain = "VGroup(block, closing, zhihu_group).arrange(DOWN, buff="
        assert chain in region, "headline block, closing and zhihu card must share one layout chain"

    def test_outro_never_uses_extreme_vertical_offsets(self):
        region = _gpu_region()[_gpu_region().index("class GPUOutroScene"):]
        for forbidden in ("shift(UP * 1.5)", "shift(UP * 1.3)", "shift(DOWN * 1.7)"):
            assert forbidden not in region, f"{forbidden} pushed content off-frame"

    def test_outro_guards_frame_height(self):
        region = _gpu_region()[_gpu_region().index("class GPUOutroScene"):]
        assert "scale_to_fit_height" in region
        assert "shift(UP * 0.55)" in region


class TestCardStrokeUniformity:
    """GPUBIOSScene, GPURankingScene, GPUBackupScene cards use accent stroke only."""

    def _scene_region(self, cls_name: str) -> str:
        src = _gpu_region()
        start = src.index(f"class {cls_name}")
        next_cls = src[start + len(f"class {cls_name}"):]
        end_match = re.search(r"\nclass \w+", next_cls)
        end = end_match.start() + start + len(f"class {cls_name}") if end_match else len(src)
        return src[start:end]

    @pytest.mark.parametrize("cls_name", [
        "GPUBIOSScene",
        "GPURankingScene",
        "GPUBackupScene",
    ])
    def test_no_semantic_color_in_cards(self, cls_name):
        region = self._scene_region(cls_name)
        forbidden = ["config.manim.success_color", "config.manim.warning_color",
                     "config.manim.error_color", "config.chart_colors"]
        found = [f for f in forbidden if f in region]
        assert not found, f"{cls_name} cards still use: {found}"
