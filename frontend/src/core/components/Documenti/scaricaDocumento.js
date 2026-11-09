import { documentiAPI } from '../../../services/documentiAPI';

/** Download a document's (first) file through the authenticated API. */
export async function scaricaDocumento(documento) {
  const res = await documentiAPI.download(documento.id);
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement('a');
  a.href = url;
  a.download = documento.nome_file || `documento-${documento.id}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export default scaricaDocumento;
