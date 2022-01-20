<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

<!--- There is no shield to get the latest version
(including pre-release versions) from PyPI,
so show the latest GitHub release instead.
--->

[![Codecov branch](https://img.shields.io/codecov/c/github/planetmint/planetmint/master.svg)](https://codecov.io/github/planetmint/planetmint?branch=master)
[![Latest release](https://img.shields.io/github/release/planetmint/planetmint/all.svg)](https://github.com/planetmint/planetmint/releases)
[![Status on PyPI](https://img.shields.io/pypi/status/planetmint.svg)](https://pypi.org/project/Planetmint/)
[![Travis branch](https://img.shields.io/travis/planetmint/planetmint/master.svg)](https://travis-ci.com/planetmint/planetmint)
[![Documentation Status](https://readthedocs.org/projects/planetmint-server/badge/?version=latest)](https://docs.planetmint.com/projects/server/en/latest/)
[![Join the chat at https://gitter.im/planetmint/planetmint](https://badges.gitter.im/planetmint/planetmint.svg)](https://gitter.im/planetmint/planetmint?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Planetmint 服务器

Planetmint 是区块链数据库. 这是 _BigchainDB 服务器_ 的仓库.

## 基础知识

* [尝试快速开始](https://docs.planetmint.com/projects/server/en/latest/quickstart.html)
* [阅读 Planetmint 2.0 白皮书](https://www.planetmint.com/whitepaper/)
* [查阅漫游指南](https://www.planetmint.com/developers/guide/)

## 运行和测试 `master` 分支的 Planetmint 服务器

运行和测试最新版本的 Planetmint 服务器非常简单. 确认你有安装最新版本的 [Docker Compose](https://docs.docker.com/compose/install/). 当你准备好了, 打开一个终端并运行:

```text
git clone https://github.com/planetmint/planetmint.git
cd planetmint
make run
```

Planetmint 应该可以通过 `http://localhost:9984/` 访问.

这里也有一些其他的命令你可以运行:

* `make start`: 通过源码和守护进程的方式运行 Planetmint (通过 `make stop` 停止).
* `make stop`: 停止运行 Planetmint.
* `make logs`: 附在日志上.
* `make test`: 运行所有单元和验收测试.
* `make test-unit-watch`: 运行所有测试并等待. 每次更改代码时都会再次运行测试.
* `make cov`: 检查代码覆盖率并在浏览器中打开结果.
* `make doc`: 生成 HTML 文档并在浏览器中打开它.
* `make clean`: 删除所有构建, 测试, 覆盖和 Python 生成物.
* `make reset`: 停止并移除所有容器. 警告: 您将丢失存储在 Planetmint 中的所有数据.

查看所有可用命令, 请运行 `make`.

## 一般人员链接

* [Planetmint.com](https://www.planetmint.com/) - Planetmint 主网站, 包括新闻订阅
* [路线图](https://github.com/planetmint/org/blob/master/ROADMAP.md)
* [博客](https://medium.com/the-planetmint-blog)
* [推特](https://twitter.com/Planetmint)

## 开发人员链接

* [所有的 Planetmint 文档](https://docs.planetmint.com/en/latest/)
* [Planetmint 服务器 文档](https://docs.planetmint.com/projects/server/en/latest/index.html)
* [CONTRIBUTING.md](.github/CONTRIBUTING.md) - how to contribute
* [社区指南](CODE_OF_CONDUCT.md)
* [公开问题](https://github.com/planetmint/planetmint/issues)
* [公开的 pull request](https://github.com/planetmint/planetmint/pulls)
* [Gitter 聊天室](https://gitter.im/planetmint/planetmint)

## 法律声明

* [许可](LICENSES.md) - 开源代码 & 开源内容
* [印记](https://www.planetmint.com/imprint/)
* [联系我们](https://www.planetmint.com/contact/)
