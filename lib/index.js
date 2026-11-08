/**
 * dsh-moduleapi — configuration bundle for DeepSeek Harness.
 *
 * The registration itself happens through `cordis.patch.yml` (the bundle
 * patch, applied by the profile loader). This module exists so the package
 * resolves as a normal cordis entry; it performs no runtime work.
 */
export default function dshModuleapi() {
  // no-op — see cordis.patch.yml
}
