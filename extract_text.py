#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 转 Markdown 工具
使用 PP-StructureV3 处理 PDF 文件并合并为单个 Markdown 文件
支持只提取图表（柱状图、折线图等）图片
"""

import argparse
import sys
from pathlib import Path

try:
    from paddleocr import PPStructureV3
except ImportError:
    print("错误: 未安装 paddleocr，请运行: pip install paddleocr[doc-parser]")
    sys.exit(1)


def process_pdf_to_markdown(
    input_file: str,
    output_dir: str = "./output",
    use_doc_orientation_classify: bool = False,
    use_doc_unwarping: bool = False,
    use_textline_orientation: bool = False,
    device: str = "cpu",
    extract_charts_only: bool = False,
):
    """
    处理 PDF 文件并转换为单个 Markdown 文件

    Args:
        input_file: PDF 文件路径
        output_dir: 输出目录
        use_doc_orientation_classify: 是否使用文档方向分类（自动识别文档的四个方向：0°、90°、180°、270°）
        use_doc_unwarping: 是否使用文档矫正（修正文档拍摄或扫描过程中的几何扭曲、倾斜、透视变形等问题）
        use_textline_orientation: 是否使用文本行方向分类
        device: 设备类型 ('cpu' 或 'gpu')
        extract_charts_only: 是否只提取图表图片（柱状图、折线图等）
    """
    # 检查输入文件是否存在
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)

    if not input_path.suffix.lower() == ".pdf":
        print(f"警告: 输入文件不是 PDF 格式: {input_file}")

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {output_path.absolute()}")

    # 初始化 PP-StructureV3 产线
    print("正在初始化 PP-StructureV3 产线...")
    try:
        pipeline = PPStructureV3(
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation,
            device=device,
            use_chart_recognition=True,  # 启用图表识别
        )
        print("产线初始化完成")
    except Exception as e:
        print(f"错误: 初始化产线失败: {e}")
        sys.exit(1)

    # 处理 PDF 文件
    print(f"正在处理 PDF 文件: {input_file}")
    try:
        output = pipeline.predict(input=str(input_path))
        print(f"处理完成，共 {len(output)} 页")
    except Exception as e:
        print(f"错误: 处理 PDF 失败: {e}")
        sys.exit(1)

    # 收集所有页面的 Markdown 信息
    print("正在合并页面...")
    markdown_list = []
    markdown_images = []
    chart_image_paths = set()  # 存储图表图片路径

    for i, res in enumerate(output, 1):
        print(f"  处理第 {i}/{len(output)} 页...")
        try:
            md_info = res.markdown
            markdown_list.append(md_info)
            
            # 如果只提取图表，需要从 JSON 结果中识别图表区域
            if extract_charts_only:
                try:
                    json_data = res.json
                    parsing_res_list = json_data.get("res", {}).get("parsing_res_list", [])
                    
                    # 查找所有图表区域
                    for parsing_res in parsing_res_list:
                        block_label = parsing_res.get("block_label", "")
                        if block_label == "chart":
                            # 图表区域的内容可能包含图片路径信息
                            block_content = parsing_res.get("block_content", "")
                            # 从 markdown 文本中提取图片路径
                            # 通常图片路径格式为: imgs/img_in_xxx.jpg
                            import re
                            img_paths = re.findall(r'imgs/img_in[^)]+\.jpg', block_content)
                            chart_image_paths.update(img_paths)
                            
                            # 也可以尝试从 block_bbox 匹配图片
                            # 但更简单的方法是从 markdown_images 中查找
                except Exception as e:
                    print(f"  警告: 解析第 {i} 页的图表信息时出错: {e}")
            
            # 保存所有图片信息（如果 extract_charts_only=False，则保存所有图片）
            if not extract_charts_only:
                markdown_images.append(md_info.get("markdown_images", {}))
            else:
                # 只保存图表图片
                page_images = md_info.get("markdown_images", {})
                filtered_images = {}
                for path, image in page_images.items():
                    # 检查路径是否在图表图片路径集合中
                    # 或者检查路径是否包含图表相关的关键词
                    if path in chart_image_paths or any(
                        keyword in path.lower() 
                        for keyword in ["chart", "图表", "img_in_chart"]
                    ):
                        filtered_images[path] = image
                markdown_images.append(filtered_images)
                
        except Exception as e:
            print(f"  警告: 处理第 {i} 页时出错: {e}")
            continue

    # 合并所有页面的 Markdown
    print("正在合并 Markdown 内容...")
    try:
        markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)
    except Exception as e:
        print(f"错误: 合并 Markdown 失败: {e}")
        sys.exit(1)

    # 保存 Markdown 文件
    mkd_file_path = output_path / f"{input_path.stem}.md"
    try:
        with open(mkd_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_texts)
        print(f"Markdown 文件已保存: {mkd_file_path.absolute()}")
    except Exception as e:
        print(f"错误: 保存 Markdown 文件失败: {e}")
        sys.exit(1)

    # 保存图片
    print("正在保存提取的图片...")
    image_count = 0
    for item in markdown_images:
        if item:
            for path, image in item.items():
                try:
                    file_path = output_path / path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(file_path)
                    image_count += 1
                    if extract_charts_only:
                        print(f"  已保存图表图片: {path}")
                except Exception as e:
                    print(f"  警告: 保存图片失败 {path}: {e}")
                    continue

    if image_count > 0:
        chart_type = "图表" if extract_charts_only else ""
        print(f"已保存 {image_count} 张{chart_type}图片到输出目录")
    else:
        chart_type = "图表" if extract_charts_only else ""
        print(f"未提取到{chart_type}图片")

    print("\n处理完成！")
    print(f"Markdown 文件: {mkd_file_path.absolute()}")
    print(f"输出目录: {output_path.absolute()}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用 PP-StructureV3 将 PDF 文件转换为 Markdown 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  python extract_text.py input.pdf

  # 指定输出目录
  python extract_text.py input.pdf -o ./my_output

  # 启用文档方向分类和文档矫正
  python extract_text.py input.pdf --use-doc-orientation --use-doc-unwarping

  # 使用 GPU
  python extract_text.py input.pdf --device gpu

  # 只提取图表图片
  python extract_text.py input.pdf --extract-charts-only
        """,
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="输入的 PDF 文件路径",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./output",
        help="输出目录 (默认: ./output)",
    )

    parser.add_argument(
        "--use-doc-orientation",
        action="store_true",
        help="启用文档方向分类",
    )

    parser.add_argument(
        "--use-doc-unwarping",
        action="store_true",
        help="启用文档图像矫正",
    )

    parser.add_argument(
        "--use-textline-orientation",
        action="store_true",
        help="启用文本行方向分类",
    )

    parser.add_argument(
        "--device",
        type=str,
        choices=["cpu", "gpu"],
        default="cpu",
        help="使用的设备 (默认: cpu)",
    )

    parser.add_argument(
        "--extract-charts-only",
        action="store_true",
        help="只提取图表图片（柱状图、折线图等）",
    )

    args = parser.parse_args()

    # 执行处理
    process_pdf_to_markdown(
        input_file=args.input_file,
        output_dir=args.output,
        use_doc_orientation_classify=args.use_doc_orientation,
        use_doc_unwarping=args.use_doc_unwarping,
        use_textline_orientation=args.use_textline_orientation,
        device=args.device,
        extract_charts_only=args.extract_charts_only,
    )


if __name__ == "__main__":
    main()

