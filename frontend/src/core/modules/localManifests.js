export async function loadLocalModuleManifests() {
  const manifests = {}
  const manifestModules = import.meta.glob('/src/modules/*/manifest.js')

  const entries = Object.entries(manifestModules)
  for (const [path, loader] of entries) {
    try {
      const manifestModule = await loader()
      const manifest = manifestModule.manifest || manifestModule.default
      if (!manifest?.id) {
        continue
      }
      manifests[manifest.id] = {
        ...manifest,
        displayName: manifest.displayName || manifest.name,
      }
    } catch (error) {
      console.warn(`[LocalManifests] Failed to load ${path}:`, error)
    }
  }

  return manifests
}
