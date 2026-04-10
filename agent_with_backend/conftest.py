"""自定义pytest配置，禁用有问题的ROS插件"""
import sys

# 尝试在插件加载前禁用ROS插件
# 这个方法在pytest_configure钩子中执行

def pytest_configure(config):
    """配置pytest，尝试禁用ROS插件"""
    # 检查是否有问题的插件
    plugin_manager = config.pluginmanager

    # 尝试从插件管理器中移除有问题的插件
    problematic_plugins = [
        'launch_testing_ros_pytest_entrypoint',
        'launch_testing_ros',
        'launch_testing'
    ]

    for plugin_name in problematic_plugins:
        # 检查插件是否已注册
        try:
            import importlib
            module = importlib.import_module(plugin_name)
            if plugin_manager.is_registered(module):
                print(f"取消注册插件: {plugin_name}")
                plugin_manager.unregister(module)
        except ImportError:
            pass
        except Exception as e:
            print(f"取消注册插件 {plugin_name} 时出错: {e}")

    # 也尝试通过设置属性来阻止插件验证错误
    # 这是针对pytest 9.0.2的临时解决方案
    try:
        # 尝试修改pluginmanager的check_pending方法
        original_check_pending = plugin_manager.check_pending

        def patched_check_pending():
            try:
                return original_check_pending()
            except Exception as e:
                if 'pytest_launch_collect_makemodule' in str(e):
                    print(f"忽略插件验证错误: {e}")
                    return
                raise

        plugin_manager.check_pending = patched_check_pending
    except Exception as e:
        print(f"无法修补pluginmanager: {e}")