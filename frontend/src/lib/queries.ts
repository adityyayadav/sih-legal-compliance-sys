import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type {
  DashboardStats,
  DetailedScan,
  Page,
  Product,
  ScanStatusResponse,
  ScanSummary,
} from "./types";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: async () => (await api.get<DashboardStats>("/api/dashboard/stats")).data,
  });
}

export function useProducts() {
  return useQuery({
    queryKey: ["products"],
    queryFn: async () => (await api.get<Product[]>("/api/products")).data,
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; category: string; brand?: string }) =>
      (await api.post<Product>("/api/products", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

export interface ScanQuery {
  page: number;
  size: number;
  status?: string;
  productId?: string;
  from?: string;
  to?: string;
}

export function useScans(q: ScanQuery) {
  return useQuery({
    queryKey: ["scans", q],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: q.page,
        size: q.size,
        sort: "createdAt,desc",
      };
      if (q.status) params.status = q.status;
      if (q.productId) params.productId = q.productId;
      if (q.from) params.from = q.from;
      if (q.to) params.to = q.to;
      return (await api.get<Page<ScanSummary>>("/api/scans", { params })).data;
    },
  });
}

export function useScanDetail(id: string | undefined) {
  return useQuery({
    queryKey: ["scan", id, "detail"],
    enabled: !!id,
    queryFn: async () => (await api.get<DetailedScan>(`/api/scans/${id}/detailed`)).data,
    refetchInterval: (query) => {
      const st = query.state.data?.scan.status;
      return st === "PENDING" || st === "PROCESSING" ? 1500 : false;
    },
  });
}

export function useScanStatus(id: string | undefined, poll: boolean) {
  return useQuery({
    queryKey: ["scan", id, "status"],
    enabled: !!id,
    refetchInterval: poll ? 1500 : false,
    queryFn: async () => (await api.get<ScanStatusResponse>(`/api/scans/${id}/status`)).data,
  });
}

export function useSubmitScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, productId }: { file: File; productId: string }) => {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("productId", productId);
      return (await api.post<ScanStatusResponse>("/api/scans", fd)).data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scans"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export async function downloadScanPdf(id: string) {
  const res = await api.get(`/api/scans/${id}/report/pdf`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `compliance-report-${id}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
