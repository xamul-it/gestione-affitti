import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

const get = vi.fn();
vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal();
  const axios = actual.default;
  return {
    ...actual,
    default: {
      ...axios,
      isCancel: axios.isCancel,
      create: () => ({ get, interceptors: { request: { use: () => {} } } }),
    },
  };
});

const { CanceledError } = await import('axios');
const { useEntityCRUD } = await import('./useEntityCRUD');

describe('useEntityCRUD.fetchAll', () => {
  beforeEach(() => get.mockReset());

  it('resolves quietly when its request is cancelled by a newer one', async () => {
    let rejectFirst;
    get
      .mockImplementationOnce(() => new Promise((_, reject) => { rejectFirst = reject; }))
      .mockResolvedValueOnce({ data: [{ id: 1 }] });
    const { result } = renderHook(() => useEntityCRUD('/x/', { autoFetch: false }));

    let first;
    await act(async () => { first = result.current.fetchAll(); });
    let second;
    await act(async () => {
      second = result.current.fetchAll();
      rejectFirst(new CanceledError());
    });

    await expect(first).resolves.toBeUndefined();
    await expect(second).resolves.toEqual([{ id: 1 }]);
    await waitFor(() => expect(result.current.data).toEqual([{ id: 1 }]));
    expect(result.current.error).toBeNull();
  });

  it('still rejects on a real error', async () => {
    get.mockRejectedValueOnce(Object.assign(new Error('boom'), { response: { status: 500, data: {} } }));
    const { result } = renderHook(() => useEntityCRUD('/x/', { autoFetch: false }));
    await act(async () => {
      await expect(result.current.fetchAll()).rejects.toThrow('boom');
    });
  });
});
