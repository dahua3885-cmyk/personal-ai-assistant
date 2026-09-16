# 第三方源码

默认桥接：chenhg5/cc-connect，vendor/cc-connect 固定 v1.4.1 / 5d4c96dd12774574369e75b60084140101c9a59a。npm/package.json 声明 MIT，固定标签根目录未包含 LICENSE，保留独立子模块来源，不使用本项目许可替代其授权。以下两个项目仅为可选候选。

两个项目均使用 MIT，来源地址记录在 .gitmodules，Git 子模块固定提交：

- op7418/Claude-to-IM：d93a8b447c453829ac4bbc6a7f721e42bf037147，许可见 vendor/Claude-to-IM/LICENSE。
- op7418/Claude-to-IM-skill：536908f5e9bd65a151ca4cb4b08d3fedc1a43b4d，许可见 vendor/Claude-to-IM-skill/LICENSE。

npm 依赖使用上游 package-lock.json，分别遵循各自许可。第三方通信实现不属于本项目原创。升级需显式复核提交与依赖。
