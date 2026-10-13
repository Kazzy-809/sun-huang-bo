#!/usr/bin/env python3
"""孙—黄—薄个人系统 CLI。Python 3.8+，仅标准库。用 --help 查看命令。"""

import argparse
import datetime
import math
from pathlib import Path
import random
import sys


COMBOS = {
    (1, 1, 0): ("被舆论劝退者", "完成一个低成本的表达或交付动作。"),
    (1, 0, 1): ("碳基服务器宕机", "先调整过载与恢复，再定可持续的任务量。"),
    (0, 1, 1): ("健身房打工人", "比较真实选项，验证一个关键假设。"),
    (1, 0, 0): ("观众席常客", "缩小启动动作，同时处理疲惫与畏缩。"),
    (0, 1, 0): ("镜子里的努力", "确认自己的目标，交出一个可获反馈的成果。"),
    (0, 0, 1): ("纯莽夫", "减少无效投入，补方向与恢复。"),
    (0, 0, 0): ("增量遗民", "从最影响今天生活的一件事开始。"),
    (1, 1, 1): ("三体齐备／进入护甲压力测试期", "保留有效循环，关注下一阶段的瓶颈。"),
}


def finite_number(raw):
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("请输入数字。") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("请输入有限数字。")
    return value


def nonnegative(raw):
    value = finite_number(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("数值须大于或等于 0。")
    return value


def positive(raw):
    value = finite_number(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("数值须大于 0。")
    return value


def probability(raw):
    value = finite_number(raw)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError("概率须在 0 到 1 之间。")
    return value


def fat_percent(raw):
    value = finite_number(raw)
    if not 0 < value < 100:
        raise argparse.ArgumentTypeError("体脂比例须大于 0 且小于 100。")
    return value


def scores(raw):
    try:
        values = tuple(int(part.strip()) for part in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("按孙、薄、黄输入三个 0/1/2，例如 2,1,0。") from exc
    if len(values) != 3 or any(value not in (0, 1, 2) for value in values):
        raise argparse.ArgumentTypeError("按孙、薄、黄输入三个 0/1/2，例如 2,1,0。")
    return values


def roi_value(reward, chance, cost, evaluation, switching):
    denominator = cost + evaluation + switching
    return reward * chance / denominator if denominator > 0 else None


def body_composition(weight, fat, target=None):
    fat_mass = weight * fat / 100.0
    lean_mass = weight - fat_mass
    scenario = lean_mass / (1 - target / 100.0) if target is not None else None
    return fat_mass, lean_mass, scenario


def secretary_threshold(n):
    """Return optimal number skipped and success probability under CSP assumptions.

    For k >= 1: P(k) = k/n * sum(1/j, j=k..n-1). P(0) = 1/n.
    A single reverse pass computes all candidates without a quadratic sum.
    """
    if n < 1:
        raise ValueError("n must be positive")
    best_k, best_p, tail = 0, 1.0 / n, 0.0
    for k in range(n - 1, 0, -1):
        tail += 1.0 / k
        p = k / n * tail
        if p > best_p + 1e-15:
            best_k, best_p = k, p
    return best_k, best_p


def cmd_diag(args, parser):
    if args.scores is None:
        print("按当前问题自评：0 明显卡住；1 初步运转；2 当前够用。")
        print("顺序：孙学方向、薄肌续航、黄毛执行。未知项先保留未知，不运行组合。")
        print("用法：diag --scores 2,1,0；详细依据见 docs/05-三体耦合模型.md。")
        return
    for label, value in zip(("孙学", "薄肌", "黄毛"), args.scores):
        print("{}：{} / 2（用户自评）".format(label, value))
    title, action = COMBOS[tuple(int(value == 2) for value in args.scores)]
    print("当前卡点组合：{}".format(title))
    print("下一步：{}".format(action))
    print("这是整理自评的启发式，不是客观测评或成功概率。")


def cmd_roi(args, parser):
    before = roi_value(args.reward, args.probability, args.cost, args.evaluation, args.switching)
    print("给定假设下的 ROI 启发式；仅用于同尺度方案比较。")

    def display(label, value):
        print("{}：{}".format(label, "分母为 0，比例无定义" if value is None else "{:.4f}".format(value)))

    display("当前", before)
    if args.evaluation_after is not None:
        after = roi_value(args.reward, args.probability, args.cost, args.evaluation_after, args.switching)
        display("使用你输入的调整后评价消耗", after)
    print("概率与评分需有输入依据；收益损失幅度、责任与时间周期另行比较。")


def cmd_body(args, parser):
    fat, lean, scenario = body_composition(args.weight, args.fat, args.target_fat)
    print("依据输入体脂估计的脂肪质量：{:.2f} kg".format(fat))
    print("去脂体重：{:.2f} kg（包含肌肉、骨骼、器官和水分）".format(lean))
    if scenario is not None:
        print("假设去脂体重不变、体脂为 {:.2f}%：体重 {:.2f} kg".format(args.target_fat, scenario))
    print("仅为输入条件下的算术情景，不自动设定健康目标或减重期限。")


def cmd_37(args, parser):
    if args.n < 1:
        parser.error("--n 须为正整数。")
    if not 0 <= args.seen <= args.n:
        parser.error("--seen 须在 0 到 N 之间。")
    if not args.classical:
        print("经典模型要求：已知 N、随机顺序、无并列排序、即时单次选择、不能回头、目标为全体最优。")
        print("普通人生选择使用候选比较与截止时间；仅作经典演示时加 --classical。")
        return
    k, p = secretary_threshold(args.n)
    print("经典秘书问题：N = {}；先观察 {} 个，从第 {} 个起选择新出现的最佳者。".format(args.n, k, k + 1))
    print("在这些假设下，选到全体最优的概率：{:.4%}。".format(p))
    if args.seen == args.n:
        print("候选已全部出现；不能回头的流程中，没有剩余候选可选。")
    elif args.seen < k:
        print("当前已观察 {} 个，观察阶段还剩 {} 个。".format(args.seen, k - args.seen))
    else:
        print("下一位若优于此前所有候选则接受；否则继续。")
    print("见 docs/06-全图插眼与37%参照系.md。")


def cmd_today(args, parser):
    template = Path(__file__).resolve().parents[1] / "templates" / "daily.md"
    content = template.read_text(encoding="utf-8")
    content = content.replace("# 每日记录 · 日期", "# 每日记录 · " + datetime.date.today().isoformat(), 1)
    if args.out:
        destination = Path(args.out).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("x", encoding="utf-8") as stream:
                stream.write(content)
        except FileExistsError:
            parser.error("文件已存在，请指定新文件，或直接编辑已有记录：{}".format(destination))
        print("已写入 {}".format(destination))
    else:
        print(content, end="")


def cmd_quote(args, parser):
    print(random.choice((
        "先拿一个真实任务，让反馈接管猜测。",
        "把解释的时间拿回来，留给你想做成的事。",
        "方向值得做，就给它一段完整的注意力。",
        "恢复和行动都要安排，才能把路走长。",
        "有证据就更新，有边界就尊重，有机会就行动。",
    )))


def build_parser():
    parser = argparse.ArgumentParser(description="孙—黄—薄理论系统：自评、情景算术与每日模板。")
    sub = parser.add_subparsers(dest="command")
    diag = sub.add_parser("diag", help="整理三维自评；顺序为孙、薄、黄")
    diag.add_argument("--scores", type=scores, help="三个 0/1/2，例如 2,1,0；不提供时显示自评说明")
    diag.set_defaults(func=cmd_diag)

    roi = sub.add_parser("roi", help="按用户给定假设计算 ROI 启发式")
    roi.add_argument("--reward", type=nonnegative, required=True)
    roi.add_argument("--probability", type=probability, required=True)
    roi.add_argument("--cost", type=nonnegative, required=True)
    roi.add_argument("--evaluation", type=nonnegative, required=True)
    roi.add_argument("--switching", type=nonnegative, required=True)
    roi.add_argument("--evaluation-after", type=nonnegative)
    roi.set_defaults(func=cmd_roi)

    body = sub.add_parser("body", help="根据已提供的体脂数据做情景算术")
    body.add_argument("--weight", type=positive, required=True, help="体重 kg")
    body.add_argument("--fat", type=fat_percent, required=True, help="当前体脂百分数")
    body.add_argument("--target-fat", type=fat_percent, help="自选算术情景中的体脂百分数")
    body.set_defaults(func=cmd_body)

    secretary = sub.add_parser("37", help="经典秘书问题的离散最优阈值演示")
    secretary.add_argument("--n", type=int, required=True)
    secretary.add_argument("--seen", type=int, default=0)
    secretary.add_argument("--classical", action="store_true", help="演示已满足经典假设的模型")
    secretary.set_defaults(func=cmd_37)

    today = sub.add_parser("today", help="打印今日模板；--out 时写新文件")
    today.add_argument("--out", help="个人记录的保存路径")
    today.set_defaults(func=cmd_today)
    quote = sub.add_parser("quote", help="一条本系统原创短句")
    quote.set_defaults(func=cmd_quote)
    return parser


def ensure_chinese_output():
    """Redirected output on a non-Chinese locale (e.g. cp1252) cannot encode Chinese; fall back to UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            "孙".encode(stream.encoding or "ascii")
        except (LookupError, UnicodeEncodeError):
            stream.reconfigure(encoding="utf-8")


def main(argv=None):
    ensure_chinese_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    args.func(args, parser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
