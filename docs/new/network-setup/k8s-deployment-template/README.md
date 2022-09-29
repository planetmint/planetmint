<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->


# Kubernetes Deployment Template

.. note::

   A highly-available Kubernetes cluster requires at least five virtual machines
   (three for the master and two for your app's containers).
   Therefore we don't recommend using Kubernetes to run a Planetmint node
   if that's the only thing the Kubernetes cluster will be running.
   Instead, see our `Node Setup <../../node_setup>`_.
   If your organization already *has* a big Kubernetes cluster running many containers,
   and your organization has people who know Kubernetes,
   then this Kubernetes deployment template might be helpful.

This section outlines a way to deploy a Planetmint node (or Planetmint network)
on Microsoft Azure using Kubernetes.
You may choose to use it as a template or reference for your own deployment,
but *we make no claim that it is suitable for your purposes*.
Feel free change things to suit your needs or preferences.
