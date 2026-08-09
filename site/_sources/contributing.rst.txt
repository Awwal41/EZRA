Contributing
============

This page summarizes how to contribute to EZRA. The full guide (forking,
dev setup, coding style, gallery/site/agent PRs, and the pull-request
checklist) lives in the repository root:

`CONTRIBUTING.md <https://github.com/Awwal41/EZRA/blob/develop/CONTRIBUTING.md>`_

Branching model
---------------

* **``develop``** - default integration branch. Open feature, fix, docs,
  gallery, sites, and agents pull requests against ``develop``.
* **``main``** - stable releases. Maintainers merge ``develop`` into
  ``main`` when a batch is ready to ship.

Do not commit day-to-day feature work straight to ``main``.

Quick development setup
-----------------------

.. code-block:: bash

   git clone https://github.com/YOUR_USER/EZRA.git
   cd EZRA
   git remote add upstream https://github.com/Awwal41/EZRA.git
   git fetch upstream
   git checkout develop
   git pull upstream develop

   python -m venv .venv
   # Windows: .venv\Scripts\activate
   source .venv/bin/activate

   pip install -U pip
   pip install -e ".[dev]"
   # optional Sphinx site:
   pip install -e ".[docs]"
   ezra doctor
   pytest

Build these docs locally
------------------------

.. code-block:: bash

   pip install -e ".[docs]"
   cd docs
   make html          # Linux / macOS
   # Windows: .\make.bat html

Open ``docs/_build/html/index.html`` in a browser.

Common contribution types
-------------------------

* **Gallery model** - append an entry in
  ``src/ezra/gallery/models.yaml``, then run
  ``ezra models info <name>`` and ``pytest tests/test_gallery.py``.
* **Bug fix / CLI** - smallest change plus tests under ``tests/``;
  update README and the matching ``docs/*.md`` page if behavior changes.
* **Site profile** - ``ezra hpc init-site <cluster>``, edit
  ``EDIT ME`` fields, smoke-test with ``--dry-run``, commit
  ``sites/<cluster>/`` without secrets. See :doc:`sites` and
  :doc:`hpc`.
* **Personal agent** - follow the step-by-step in :doc:`agents`:
  ``ezra agents init``, ``ezra models recommend``, edit
  ``agent.yaml`` / ``prompt.md``, ``ezra agents check``, then
  ``ezra models download``.
* **Docs** - edit the guide under ``docs/``, keep ``index.rst`` in sync
  for new pages, and build HTML locally before opening the PR.

Pull requests
-------------

1. Branch from up-to-date ``develop``.
2. Push to your fork and open a PR with base **``develop``**.
3. Describe what changed, why, and how you tested.
4. Expect checklist items from ``CONTRIBUTING.md`` (tests, Ruff, no
   secrets/weights, docs updated when needed).

Shared backlog: `TODO.md <https://github.com/Awwal41/EZRA/blob/develop/TODO.md>`_.
