'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useFilterStore } from '../../../store/useFilterStore';
import { useAuthContext } from '../../providers';
import { apiClient } from '../../../services/apiClient';
import { useTranslations } from 'next-intl';
import { toast } from 'sonner';
import Papa from 'papaparse';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { FileSpreadsheet, FileDown, Upload, Activity, ShieldAlert, CheckCircle, RefreshCw } from 'lucide-react';
import Link from 'next/link';

type Violation = {
  id: string;
  image_url: string | null;
  timestamp: string;
  track_id: number | null;
  model_used: string | null;
  is_flagged?: boolean;
};

export default function DashboardPage() {
  const t = useTranslations('dashboard');
  const tr = useTranslations('results');
  const { accessToken } = useAuthContext();
  const dateRange = useFilterStore((state) => state.dateRange);
  const selectedModel = useFilterStore((state) => state.selectedModel);
  
  const [violations, setViolations] = useState<Violation[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // 1. Fetch violations list from REST API
  const { refetch } = useQuery({
    queryKey: ['violations', dateRange, selectedModel],
    queryFn: async () => {
      try {
        setIsSyncing(true);
        const response = await apiClient(
          `/api/v1/violations?startDate=${dateRange.startDate}&endDate=${dateRange.endDate}&model=${selectedModel}`,
          { token: accessToken }
        );
        const items = response.items || [];
        setViolations(items);
        return items;
      } catch (err) {
        console.error('Backend API list failed', err);
        toast.error('Khong the tai danh sach vi pham tu may chu.');
        throw err;
      } finally {
        setIsSyncing(false);
      }
    },
  });

  // CSV Export trigger using papaparse client-side (FR-015)
  const handleExportCSV = () => {
    if (violations.length === 0) {
      toast.warning('Không có dữ liệu vi phạm để xuất báo cáo.');
      return;
    }
    const csvData = violations.map((v) => ({
      ID: v.id,
      Timestamp: new Date(v.timestamp).toLocaleString(),
      TrackID: v.track_id || 'N/A',
      Model: v.model_used || 'yolo',
      Flagged: v.is_flagged ? 'Flagged' : 'Approved',
      ImageURL: v.image_url || 'N/A',
    }));
    const csv = Papa.unparse(csvData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `violations_report_${Date.now()}.csv`;
    link.click();
    toast.success('Báo cáo CSV được tải xuống thành công!');
  };

  // PDF Export trigger via server-side generation (FR-015)
  const handleExportPDF = async () => {
    try {
      toast.info('Đang yêu cầu kết xuất PDF từ máy chủ...');
      const response = await apiClient(
        `/api/v1/violations/pdf?startDate=${dateRange.startDate}&endDate=${dateRange.endDate}`,
        { token: accessToken }
      );
      
      // Binary pipe blob down to client
      const blob = new Blob([response], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `traffic_helmet_report_${Date.now()}.pdf`;
      link.click();
      toast.success('Tải báo cáo PDF thành công!');
    } catch (err) {
      console.warn('PDF Endpoint unavailable, generating client print preview', err);
      window.print();
    }
  };

  // Mock analytics charts data
  const hourlyData = [
    { name: '08:00', count: 14 },
    { name: '10:00', count: 25 },
    { name: '12:00', count: 8 },
    { name: '14:00', count: 19 },
    { name: '16:00', count: 32 },
    { name: '18:00', count: 45 },
    { name: '20:00', count: 12 },
  ];

  const modelData = [
    { name: 'YOLO', violations: 48, accuracy: 89 },
    { name: 'RT-DETR', violations: 32, accuracy: 94 },
    { name: 'Faster R-CNN', violations: 15, accuracy: 91 },
  ];

  const locationData = [
    { name: 'Ngã tư A', value: 45 },
    { name: 'Ngã tư B', value: 30 },
    { name: 'Vòng xoay C', value: 25 },
  ];

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b'];

  return (
    <div className="flex flex-col space-y-8 p-6 text-white max-w-7xl mx-auto">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('totalViolations')}</h1>
          <p className="text-sm text-slate-400 mt-2">
            Tổng hợp thống kê vi phạm an toàn giao thông đường bộ thời gian thực.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 hover:text-white transition cursor-pointer"
            title="Làm mới dữ liệu"
          >
            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin text-sky-400' : ''}`} />
          </button>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 font-semibold text-xs py-2.5 px-4 rounded-lg transition cursor-pointer"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            {t('exportCSV')}
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 font-semibold text-xs py-2.5 px-4 rounded-lg transition cursor-pointer"
          >
            <FileDown className="w-4 h-4 text-sky-400" />
            {t('exportPDF')}
          </button>
          <Link
            href="/upload"
            className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs py-2.5 px-4 rounded-lg transition"
          >
            <Upload className="w-4 h-4" />
            Tải lên video
          </Link>
        </div>
      </div>

      {/* Summary Cards widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg flex items-center gap-4">
          <div className="p-3 bg-rose-950/40 border border-rose-900/50 rounded-xl text-rose-500">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{t('totalViolations')}</p>
            <h3 className="text-3xl font-extrabold text-white mt-1">{violations.length}</h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg flex items-center gap-4">
          <div className="p-3 bg-sky-950/40 border border-sky-900/50 rounded-xl text-sky-400">
            <Activity className="w-8 h-8" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{t('activeFeeds')}</p>
            <h3 className="text-3xl font-extrabold text-white mt-1">4 camera</h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg flex items-center gap-4">
          <div className="p-3 bg-emerald-950/40 border border-emerald-900/50 rounded-xl text-emerald-400">
            <CheckCircle className="w-8 h-8" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{t('accuracyRate')}</p>
            <h3 className="text-3xl font-extrabold text-white mt-1">92.3%</h3>
          </div>
        </div>
      </div>

      {/* Analytical Recharts Panels (FR-013, FR-014) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend area chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <h4 className="text-sm font-semibold text-slate-200">{t('hourlyTrend')}</h4>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={hourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff' }} />
              <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#colorCount)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Location pie chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <h4 className="text-sm font-semibold text-slate-200">{t('locationBreakdown')}</h4>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={locationData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {locationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff' }} />
              <Legend verticalAlign="bottom" height={36} iconType="circle" />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model performance benchmarks compare */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
        <h4 className="text-sm font-semibold text-slate-200">{t('modelComparison')}</h4>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={modelData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} />
            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff' }} />
            <Legend />
            <Bar dataKey="violations" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Số vi phạm ghi nhận" />
            <Bar dataKey="accuracy" fill="#10b981" radius={[4, 4, 0, 0]} name="Độ chính xác (%)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Violations listing grid list */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-slate-100">{tr('violationsTitle')}</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 font-bold border-b border-slate-800">
              <tr>
                <th className="px-6 py-3 font-semibold">Hình ảnh minh chứng</th>
                <th className="px-6 py-3 font-semibold">Thời gian phát hiện</th>
                <th className="px-6 py-3 font-semibold">Mã định danh (Track ID)</th>
                <th className="px-6 py-3 font-semibold">Mô hình phân tích</th>
                <th className="px-6 py-3 font-semibold">Trạng thái phê duyệt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/50">
              {violations.length > 0 ? (
                violations.map((v) => (
                  <tr className="hover:bg-slate-800/40 transition" key={v.id}>
                    <td className="px-6 py-4">
                      {v.image_url ? (
                        <a
                          href={v.image_url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-sky-400 hover:text-sky-300 flex items-center gap-1"
                        >
                          Xem ảnh
                        </a>
                      ) : (
                        <span className="text-slate-500">Đang cập nhật...</span>
                      )}
                    </td>
                    <td className="px-6 py-4">{new Date(v.timestamp).toLocaleString()}</td>
                    <td className="px-6 py-4 font-mono">{v.track_id ?? '-'}</td>
                    <td className="px-6 py-4 capitalize">{v.model_used || 'yolo'}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          v.is_flagged
                            ? 'bg-rose-950/30 text-rose-400 border border-rose-900/40'
                            : 'bg-emerald-950/30 text-emerald-400 border border-emerald-900/40'
                        }`}
                      >
                        {v.is_flagged ? tr('flagged') : 'Approved'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-6 py-12 text-center text-slate-500 font-medium" colSpan={5}>
                    Chưa có vi phạm nào được ghi nhận.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
