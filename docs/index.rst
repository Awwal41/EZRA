EZRA documentation
==================

**Easy Zero-setup Routing Assistant** for local and HPC LLMs — download curated
free/open models, pick ones that fit your machine, scaffold personal agents, and
stage jobs on SLURM.

This site is built with `Sphinx <https://www.sphinx-doc.org/>`_ using
**reStructuredText** (``.rst``) and **MyST Markdown** (``.md``). You can still
read the same guides as plain Markdown on GitHub under ``docs/``.

.. tip::

   Unsure which model to download? Run ``ezra models recommend chemistry``
   (or another keyword). See :doc:`models`.

Quick links
-----------

* :doc:`install` — venv, ``pip install``, ``ezra doctor``
* :doc:`models` — recommend, list, download, status
* :doc:`agents` — personal agent scaffolds (prompt + preferred models)
* :doc:`hpc` — site profiles and ``ezra hpc submit``
* :doc:`cli` — full CLI reference
* :doc:`api` — Python package reference

.. toctree::
   :maxdepth: 2
   :caption: User guides

   install
   models
   agents
   hpc
   sites
   configuration
   cli

.. toctree::
   :maxdepth: 2
   :caption: Development

   contributing
   api

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
