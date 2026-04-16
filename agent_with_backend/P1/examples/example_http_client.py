# example_http_client.py
"""
HTTP客户端使用示例。
"""

import asyncio
import logging
from ..utils.http_client import PharmacyHTTPClient

# 设置日志级别
logging.basicConfig(level=logging.INFO)


async def example_async_usage():
    """异步使用示例"""
    print("=== 异步使用示例 ===")

    # 创建客户端
    client = PharmacyHTTPClient(base_url="http://localhost:8001")

    try:
        # 1. 健康检查
        print("1. 执行健康检查...")
        health = await client.health_check_async()
        print(f"   健康状态: {health}")

        # 2. 获取药物列表
        print("2. 获取药物列表...")
        drugs = await client.get_drugs_async()
        print(f"   找到 {len(drugs)} 种药物")

        if drugs:
            # 3. 获取单个药物信息
            print("3. 获取单个药物信息...")
            drug_id = drugs[0]["id"]
            drug = await client.get_drug_by_id_async(drug_id)
            print(f"   药物详情: {drug.get('name', '未知') if drug else '未找到'}")

        # 4. 创建审批
        print("4. 创建用药审批...")
        approval_id = await client.create_approval_async(
            patient_name="张三",
            advice="建议使用布洛芬缓解头痛",
            symptoms="头痛、发热",
            age=35,
        )
        print(f"   创建的审批ID: {approval_id}")

        if approval_id:
            # 5. 获取审批详情
            print("5. 获取审批详情...")
            approval = await client.get_approval_async(approval_id)
            print(
                f"   审批状态: {approval.get('status', '未知') if approval else '未找到'}"
            )

            # 6. 获取待处理审批
            print("6. 获取待处理审批列表...")
            pending = await client.get_pending_approvals_async(limit=10)
            print(f"   待处理审批数量: {len(pending)}")

        # 7. 创建订单
        print("7. 创建药品订单...")
        order_items = [{"id": 1, "num": 2}, {"id": 2, "num": 1}]
        order_result = await client.create_order_async(order_items)
        print(
            f"   订单创建结果: {order_result.get('message', '未知') if order_result else '失败'}"
        )

    except Exception as e:
        print(f"示例执行出错: {e}")


def example_sync_usage():
    """同步使用示例"""
    print("\n=== 同步使用示例 ===")

    # 创建客户端
    client = PharmacyHTTPClient(base_url="http://localhost:8001")

    try:
        # 1. 健康检查
        print("1. 执行健康检查...")
        health = client.health_check()
        print(f"   健康状态: {health.get('backend', '未知')}")

        # 2. 获取药物列表（带过滤）
        print("2. 搜索药物'布洛芬'...")
        drugs = client.get_drugs(name_filter="布洛芬")
        print(f"   找到 {len(drugs)} 种匹配药物")

        # 3. 批准审批（示例）
        print("3. 批准审批（示例）...")
        # 注意：实际使用时需要真实的审批ID和医生ID
        # result = client.approve_approval("AP-123456", "DR-001")
        # print(f"   批准结果: {result.get('message', '未知') if result else '失败'}")
        print("   （示例跳过，需要真实审批ID）")

    except Exception as e:
        print(f"示例执行出错: {e}")


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    # 使用无效的URL测试错误处理
    client = PharmacyHTTPClient(base_url="http://invalid-server:9999")

    print("1. 测试网络错误处理...")
    drugs = await client.get_drugs_async()
    print(f"   结果: {'空列表（预期）' if drugs == [] else '异常'}")

    print("2. 测试404错误处理...")
    drug = await client.get_drug_by_id_async(99999)
    print(f"   结果: {'None（预期）' if drug is None else '异常'}")


def main():
    """主函数"""
    print("HTTP客户端使用示例")
    print("=" * 50)

    # 运行同步示例
    example_sync_usage()

    # 运行异步示例
    asyncio.run(example_async_usage())

    # 运行错误处理示例
    asyncio.run(example_error_handling())

    print("\n" + "=" * 50)
    print("示例完成！")


if __name__ == "__main__":
    main()
