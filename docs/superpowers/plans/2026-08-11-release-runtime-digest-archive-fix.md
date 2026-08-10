---
title: Runtime digest archive correction
author: Ray
description: Correct explicit runtime release-digest archive membership and bind its generated archive SHA.
status: historical-record
---

> **Historical Record**
> **Not Current Product Documentation**
> **Do Not Use As Runtime Instruction**

The v0.5.53 rehearsal proved that an export-ignored runtime digest was absent
from the generated archive. The release builder now permits only an explicit,
workflow-selected runtime digest member and rebinds the runtime archive SHA.
