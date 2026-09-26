// Loads chart-ready JSON written by the pipeline into public/data/.
// Every dataset file must carry a `source` object; charts refuse to render without one.

const base = import.meta.env.BASE_URL

export async function loadIndex() {
  const res = await fetch(`${base}data/index.json`)
  if (!res.ok) throw new Error(`index.json: HTTP ${res.status}`)
  return res.json()
}

export async function loadDataset(id) {
  const res = await fetch(`${base}data/${id}.json`)
  if (!res.ok) return null
  const data = await res.json()
  if (!data.source?.id || !data.source?.url) {
    throw new Error(`${id}.json has no source attribution`)
  }
  return data
}
