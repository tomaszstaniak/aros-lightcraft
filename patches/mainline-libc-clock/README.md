# Mainline Rust libc condition-attribute clock declarations

Base: jonx/AROS2eb81b402b0d3de6d0b068ce74fdb6eb653f2d60, the native Rust integration branch associated with AROS PR1800. This changes its maintained libc0.2.190 patch, adding the two existing pthread2 API declarations. The getter preserves const and both use clockid_t from the selected SDK.

The pthread clock implementation already exists upstream (AROS PR1305); this is a binding fix, not a replacement pthread implementation. The patch adds declarations to the existing pthread clock API. Native execution remains unverified because the available mainline runtime is older than the selected profile. No other architecture is claimed.

Submitted as a draft: https://github.com/jonx/AROS/pull/1. Native execution remains unverified.
