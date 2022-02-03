<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Write Docs

If you're writing code, you should also update any related docs. However, you might want to write docs only, such as:

- General explainers
- Tutorials
- Courses
- Code explanations
- How Planetmint relates to other blockchain things
- News from recent events

You can certainly do that!

- The docs for Planetmint Server live under ``planetmint/docs/`` in the ``planetmint/planetmint`` repo.
- There are docs for the Python driver under ``planetmint-driver/docs/`` in the ``planetmint/planetmint-driver`` repo.
- There are docs for the JavaScript driver under ``planetmint/js-bigchaindb-driver`` in the ``planetmint/js-bigchaindb-driver`` repo.
- The source code for the Planetmint website is in a private repo, but we can give you access if you ask.

The [Planetmint Transactions Specs](https://github.com/planetmint/PEPs/tree/master/tx-specs/) (one for each spec version) are in the ``planetmint/PEPs`` repo.

You can write the docs using Markdown (MD) or RestructuredText (RST). Sphinx can understand both. RST is more powerful.

ReadTheDocs will automatically rebuild the docs whenever a commit happens on the ``master`` branch, or on one of the other branches that it is monitoring.
