'use client';

import { useState, useEffect, useMemo, Fragment } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { toast, Toaster } from 'sonner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  Pencil,
  Trash2,
  Plus,
  Loader2,
  Search,
  X,
  Package,
  Wrench,
  MapPin,
  Calendar,
  DollarSign,
  Tag,
  Barcode,
  Building2,
  User,
  AlertCircle,
  Download,
  Grid3x3,
  Table as TableIcon,
  ChevronDown,
  ChevronUp,
  HardHat,
  Hammer,
  Settings,
  Maximize2,
  Minimize2,
} from 'lucide-react';

// =============== IMPORTED COMPONENTS ===============
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';

// =============== CONSTANTS ===============
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const CATEGORIES = [
  'Audio',
  'Visual',
  'Lighting',
  'Furniture',
  'Musical Instruments',
  'Vehicles',
  'Kitchen',
  'Office',
  'HVAC',
  'Safety',
  'Cleaning',
  'Other',
];

const STATUSES = [
  { value: 'available', label: 'Available', color: 'bg-green-100 text-green-800' },
  { value: 'in_use', label: 'In Use', color: 'bg-blue-100 text-blue-800' },
  { value: 'maintenance', label: 'Maintenance', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'damaged', label: 'Damaged', color: 'bg-red-100 text-red-800' },
  { value: 'retired', label: 'Retired', color: 'bg-gray-100 text-gray-800' },
];

const CONDITIONS = [
  { value: 'excellent', label: 'Excellent', color: 'bg-green-100 text-green-800' },
  { value: 'good', label: 'Good', color: 'bg-blue-100 text-blue-800' },
  { value: 'fair', label: 'Fair', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'poor', label: 'Poor', color: 'bg-red-100 text-red-800' },
];

// =============== TYPES ===============
interface Equipment {
  id: string;
  name: string;
  description: string;
  category: string;
  serial_number: string;
  model_number: string;
  manufacturer: string;
  status: string;
  condition: string;
  purchase_date: string;
  purchase_price: number;
  supplier: string;
  location: string;
  assigned_to: string;
  last_maintenance: string;
  next_maintenance: string;
  notes: string;
  created_at?: string;
  updated_at?: string;
}

interface EquipmentStats {
  total: number;
  available: number;
  in_use: number;
  maintenance: number;
  damaged: number;
  need_maintenance_soon: number;
  total_value: number;
}

// =============== API HELPER FUNCTIONS ===============
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log('Fetching:', url);
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    console.log('Response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response:', errorText);
      
      try {
        const errorJson = JSON.parse(errorText);
        throw new Error(errorJson.detail || `API error: ${response.status}`);
      } catch {
        throw new Error(errorText || `API error: ${response.status}`);
      }
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      return data;
    }
    return {} as T;
  } catch (error) {
    console.error('Fetch error details:', error);
    throw error;
  }
}

// =============== API FUNCTIONS ===============
async function getEquipment(params?: {
  search?: string;
  category?: string;
  status?: string;
  location?: string;
  assigned_to?: string;
  limit?: number;
  offset?: number;
}): Promise<Equipment[]> {
  const queryParams = new URLSearchParams();
  if (params?.search) queryParams.append('search', params.search);
  if (params?.category) queryParams.append('category', params.category);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.location) queryParams.append('location', params.location);
  if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const data = await fetchAPI<any[]>(`/equipment/?${queryParams.toString()}`);
  return Array.isArray(data) ? data : [];
}

async function getEquipmentCount(params?: {
  search?: string;
  category?: string;
  status?: string;
  location?: string;
  assigned_to?: string;
}): Promise<number> {
  const queryParams = new URLSearchParams();
  if (params?.search) queryParams.append('search', params.search);
  if (params?.category) queryParams.append('category', params.category);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.location) queryParams.append('location', params.location);
  if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);

  return fetchAPI<number>(`/equipment/count?${queryParams.toString()}`);
}

async function getEquipmentStats(): Promise<EquipmentStats> {
  try {
    const data = await fetchAPI<any>('/equipment/stats/overview');
    return {
      total: data?.total || 0,
      available: data?.available || 0,
      in_use: data?.in_use || 0,
      maintenance: data?.maintenance || 0,
      damaged: data?.damaged || 0,
      need_maintenance_soon: data?.need_maintenance_soon || 0,
      total_value: data?.total_value || 0,
    };
  } catch {
    return {
      total: 0,
      available: 0,
      in_use: 0,
      maintenance: 0,
      damaged: 0,
      need_maintenance_soon: 0,
      total_value: 0,
    };
  }
}

async function createEquipment(equipment: Partial<Equipment>): Promise<Equipment> {
  return fetchAPI<any>('/equipment/', {
    method: 'POST',
    body: JSON.stringify(equipment),
  });
}

async function updateEquipment(id: string, equipment: Partial<Equipment>): Promise<Equipment> {
  return fetchAPI<any>(`/equipment/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(equipment),
  });
}

async function deleteEquipment(id: string): Promise<void> {
  await fetchAPI(`/equipment/${id}`, {
    method: 'DELETE',
  });
}

// =============== MAIN PAGE ===============
export default function EquipmentPage() {
  const router = useRouter();
  
  // View mode
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');

  // Data
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingItem, setEditingItem] = useState<Equipment | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [stats, setStats] = useState<EquipmentStats>({
    total: 0,
    available: 0,
    in_use: 0,
    maintenance: 0,
    damaged: 0,
    need_maintenance_soon: 0,
    total_value: 0,
  });

  // Expanded items
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(50);
  const [totalCount, setTotalCount] = useState(0);

  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [churchName, setChurchName] = useState('Grace Community Church');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    serial_number: '',
    model_number: '',
    manufacturer: '',
    status: 'available',
    condition: 'good',
    purchase_date: '',
    purchase_price: 0,
    supplier: '',
    location: '',
    assigned_to: '',
    last_maintenance: '',
    next_maintenance: '',
    notes: '',
  });

  // Load auth
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    const church = localStorage.getItem('church');
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setIsLoggedIn(true);
        setUser(parsedUser);
        if (church) setChurchName(church);
      } catch (error) {
        // ignore
      }
    }
  }, []);

  // Test API connection on mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        console.log('Testing API connection to:', `${API_BASE_URL}/health`);
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
          console.log('API connection successful');
        } else {
          console.error('API connection failed:', res.status);
          toast.error('Cannot connect to backend server');
        }
      } catch (error) {
        console.error('API connection error:', error);
        toast.error('Cannot connect to backend server');
      }
    };
    testConnection();
  }, []);

  // Fetch data
  useEffect(() => {
    fetchEquipment();
    fetchStats();
  }, [searchTerm, selectedCategory, selectedStatus, selectedLocation, currentPage]);

  const fetchEquipment = async () => {
    setLoading(true);
    try {
      const data = await getEquipment({
        search: searchTerm || undefined,
        category: selectedCategory && selectedCategory !== 'all' ? selectedCategory : undefined,
        status: selectedStatus && selectedStatus !== 'all' ? selectedStatus : undefined,
        location: selectedLocation || undefined,
        limit: pageSize,
        offset: currentPage * pageSize,
      });
      setEquipment(data);
      
      const count = await getEquipmentCount({
        search: searchTerm || undefined,
        category: selectedCategory && selectedCategory !== 'all' ? selectedCategory : undefined,
        status: selectedStatus && selectedStatus !== 'all' ? selectedStatus : undefined,
        location: selectedLocation || undefined,
      });
      setTotalCount(count);
    } catch (error) {
      console.error('Failed to fetch equipment:', error);
      toast.error('Failed to load equipment');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await getEquipmentStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const toggleExpanded = (id: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Expand all items
  const expandAll = () => {
    setExpandedItems(new Set(equipment.map(item => item.id)));
  };

  // Collapse all items
  const collapseAll = () => {
    setExpandedItems(new Set());
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedCategory('all');
    setSelectedStatus('all');
    setSelectedLocation('');
    setCurrentPage(0);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: '',
      serial_number: '',
      model_number: '',
      manufacturer: '',
      status: 'available',
      condition: 'good',
      purchase_date: '',
      purchase_price: 0,
      supplier: '',
      location: '',
      assigned_to: '',
      last_maintenance: '',
      next_maintenance: '',
      notes: '',
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    if (!formData.name.trim()) {
      toast.error('Equipment name is required');
      setSaving(false);
      return;
    }

    try {
      if (editingItem) {
        await updateEquipment(editingItem.id, formData);
        toast.success('Equipment updated successfully');
      } else {
        await createEquipment(formData);
        toast.success('Equipment added successfully');
      }
      
      setDialogOpen(false);
      resetForm();
      setEditingItem(null);
      await fetchEquipment();
      await fetchStats();
    } catch (error: any) {
      console.error('Failed to save equipment:', error);
      toast.error(error.message || 'Failed to save equipment');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item: Equipment) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      description: item.description || '',
      category: item.category || '',
      serial_number: item.serial_number || '',
      model_number: item.model_number || '',
      manufacturer: item.manufacturer || '',
      status: item.status || 'available',
      condition: item.condition || 'good',
      purchase_date: item.purchase_date || '',
      purchase_price: item.purchase_price || 0,
      supplier: item.supplier || '',
      location: item.location || '',
      assigned_to: item.assigned_to || '',
      last_maintenance: item.last_maintenance || '',
      next_maintenance: item.next_maintenance || '',
      notes: item.notes || '',
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this equipment?')) return;
    
    try {
      await deleteEquipment(id);
      toast.success('Equipment deleted successfully');
      await fetchEquipment();
      await fetchStats();
    } catch (error: any) {
      console.error('Failed to delete equipment:', error);
      toast.error(error.message || 'Failed to delete equipment');
    }
  };

  const openNewDialog = () => {
    setEditingItem(null);
    resetForm();
    setDialogOpen(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('church');
    setIsLoggedIn(false);
    setUser(null);
    window.location.reload();
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    const s = STATUSES.find(s => s.value === status);
    return s ? (
      <Badge className={s.color}>{s.label}</Badge>
    ) : (
      <Badge>{status}</Badge>
    );
  };

  // Get condition badge
  const getConditionBadge = (condition: string) => {
    const c = CONDITIONS.find(c => c.value === condition);
    return c ? (
      <Badge className={c.color}>{c.label}</Badge>
    ) : (
      <Badge>{condition}</Badge>
    );
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Format date
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  // Pagination
  const totalPages = Math.ceil(totalCount / pageSize);
  const startItem = currentPage * pageSize + 1;
  const endItem = Math.min((currentPage + 1) * pageSize, totalCount);

  if (loading && equipment.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-200 border-t-purple-600" />
          <p className="text-purple-800 text-sm font-medium">Loading equipment...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Toaster position="top-right" richColors />

      <Header
        isLoggedIn={isLoggedIn}
        user={user}
        churchName={churchName}
        onLogout={handleLogout}
      />

      {/* Background */}
      <div className="fixed inset-0 z-0">
        <div
          className="absolute inset-0 bg-gradient-to-br from-purple-900/40 to-blue-900/30"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1511895426328-dc8714191300?auto=format&fit=crop&q=80&w=2070')",
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            opacity: 0.9,
            filter: 'brightness(1.05) contrast(1.1) saturate(1.1)',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-purple-900/40 via-transparent to-blue-900/30" />
      </div>

      <div className="relative z-10 min-h-screen">
        <main className="container mx-auto py-10 px-4">
          {/* Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white drop-shadow-lg">
                Equipment Directory
              </h1>
              <p className="text-purple-100 mt-1">
                Showing {equipment.length} of {totalCount} items
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setViewMode('table')}
                className={`bg-white/10 backdrop-blur-sm border-white/30 ${
                  viewMode === 'table' ? 'bg-white/30 text-white' : 'text-white/70 hover:text-white'
                }`}
              >
                <TableIcon className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setViewMode('grid')}
                className={`bg-white/10 backdrop-blur-sm border-white/30 ${
                  viewMode === 'grid' ? 'bg-white/30 text-white' : 'text-white/70 hover:text-white'
                }`}
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                onClick={openNewDialog}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-lg"
              >
                <Plus className="h-4 w-4 mr-2" /> Add Equipment
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3 mb-6">
            <Card className="bg-white/80 backdrop-blur-sm border-purple-200/40">
              <CardContent className="p-3 text-center">
                <Package className="h-5 w-5 text-purple-700 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
                <p className="text-xs text-gray-500">Total</p>
              </CardContent>
            </Card>
            <Card className="bg-white/80 backdrop-blur-sm border-green-200/40">
              <CardContent className="p-3 text-center">
                <div className="h-5 w-5 text-green-700 mx-auto mb-1">✓</div>
                <p className="text-2xl font-bold text-gray-800">{stats.available}</p>
                <p className="text-xs text-gray-500">Available</p>
              </CardContent>
            </Card>
            <Card className="bg-white/80 backdrop-blur-sm border-blue-200/40">
              <CardContent className="p-3 text-center">
                <User className="h-5 w-5 text-blue-700 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-800">{stats.in_use}</p>
                <p className="text-xs text-gray-500">In Use</p>
              </CardContent>
            </Card>
            <Card className="bg-white/80 backdrop-blur-sm border-yellow-200/40">
              <CardContent className="p-3 text-center">
                <Wrench className="h-5 w-5 text-yellow-700 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-800">{stats.maintenance}</p>
                <p className="text-xs text-gray-500">Maintenance</p>
              </CardContent>
            </Card>
            <Card className="bg-white/80 backdrop-blur-sm border-red-200/40">
              <CardContent className="p-3 text-center">
                <AlertCircle className="h-5 w-5 text-red-700 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-800">{stats.damaged}</p>
                <p className="text-xs text-gray-500">Damaged</p>
              </CardContent>
            </Card>
            <Card className="bg-white/80 backdrop-blur-sm border-orange-200/40">
              <CardContent className="p-3 text-center">
                <Calendar className="h-5 w-5 text-orange-700 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-800">{stats.need_maintenance_soon}</p>
                <p className="text-xs text-gray-500">Due Soon</p>
              </CardContent>
            </Card>
            <Card className="bg-white/80 backdrop-blur-sm border-indigo-200/40">
              <CardContent className="p-3 text-center">
                <DollarSign className="h-5 w-5 text-indigo-700 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-800">{formatCurrency(stats.total_value)}</p>
                <p className="text-xs text-gray-500">Total Value</p>
              </CardContent>
            </Card>
          </div>

          {/* Search and Filters */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 mb-6 border border-purple-200/40 shadow-lg">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by name, serial, model, manufacturer..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-10 bg-white/80 border-purple-200"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              {/* Expand/Collapse All */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={expandAll}
                  className="bg-white/80 border-purple-200"
                >
                  <Maximize2 className="h-4 w-4 mr-2" />
                  Expand All
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={collapseAll}
                  className="bg-white/80 border-purple-200"
                >
                  <Minimize2 className="h-4 w-4 mr-2" />
                  Collapse All
                </Button>
              </div>

              {/* Category Filter */}
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-full lg:w-[180px] bg-white/80 border-purple-200">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {CATEGORIES.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Status Filter */}
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-full lg:w-[150px] bg-white/80 border-purple-200">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  {STATUSES.map(s => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Clear Filters */}
              {(searchTerm || selectedCategory !== 'all' || selectedStatus !== 'all' || selectedLocation) && (
                <Button variant="ghost" onClick={clearFilters} className="text-purple-700 hover:text-purple-800">
                  Clear Filters
                </Button>
              )}
            </div>
          </div>

          {/* View: Table or Grid */}
          {viewMode === 'table' ? (
            /* ========== TABLE VIEW ========== */
            <div>
              <Card className="border-purple-200/40 bg-white/90 backdrop-blur-sm shadow-xl overflow-hidden">
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader className="bg-gradient-to-r from-purple-100/80 to-blue-100/80">
                        <TableRow>
                          <TableHead className="w-10"></TableHead>
                          <TableHead>Equipment</TableHead>
                          <TableHead>Category</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Condition</TableHead>
                          <TableHead>Location</TableHead>
                          <TableHead>Assigned To</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {loading ? (
                          <TableRow>
                            <TableCell colSpan={8} className="text-center py-12">
                              <Loader2 className="h-8 w-8 animate-spin mx-auto text-purple-600" />
                            </TableCell>
                          </TableRow>
                        ) : equipment.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={8} className="text-center py-12 text-gray-500">
                              <div className="flex flex-col items-center gap-2">
                                <Package className="h-8 w-8 text-gray-400" />
                                <p>No equipment found.</p>
                                <Button variant="link" onClick={clearFilters} className="text-purple-600">
                                  Clear filters
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ) : (
                          equipment.map((item) => (
                            <Fragment key={item.id}>
                              {/* Main row */}
                              <TableRow className="hover:bg-purple-50/50 transition">
                                <TableCell>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => toggleExpanded(item.id)}
                                  >
                                    {expandedItems.has(item.id) ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-100">
                                      <Package className="h-5 w-5 text-purple-700" />
                                    </div>
                                    <div>
                                      <p className="font-medium text-gray-800">{item.name}</p>
                                      <p className="text-xs text-gray-500">
                                        {item.serial_number && `SN: ${item.serial_number}`}
                                        {item.model_number && ` · Model: ${item.model_number}`}
                                      </p>
                                    </div>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className="bg-purple-50">
                                    {item.category || '—'}
                                  </Badge>
                                </TableCell>
                                <TableCell>{getStatusBadge(item.status)}</TableCell>
                                <TableCell>{getConditionBadge(item.condition)}</TableCell>
                                <TableCell>{item.location || '—'}</TableCell>
                                <TableCell>{item.assigned_to || '—'}</TableCell>
                                <TableCell className="text-right space-x-1">
                                  <Button variant="ghost" size="icon" onClick={() => handleEdit(item)} className="hover:bg-purple-100">
                                    <Pencil className="h-4 w-4 text-purple-700" />
                                  </Button>
                                  <Button variant="ghost" size="icon" onClick={() => handleDelete(item.id)} className="hover:bg-red-100">
                                    <Trash2 className="h-4 w-4 text-red-600" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                              
                              {/* Expanded details */}
                              {expandedItems.has(item.id) && (
                                <TableRow className="bg-purple-50/30 border-t-0">
                                  <TableCell colSpan={8} className="p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                      {/* Basic Info */}
                                      <div className="space-y-2">
                                        <h4 className="font-semibold text-purple-800 text-sm">Basic Info</h4>
                                        <div className="space-y-1 text-sm">
                                          {item.description && <p><span className="text-gray-500">Description:</span> {item.description}</p>}
                                          {item.manufacturer && <p><span className="text-gray-500">Manufacturer:</span> {item.manufacturer}</p>}
                                          {item.serial_number && <p><span className="text-gray-500">Serial:</span> {item.serial_number}</p>}
                                          {item.model_number && <p><span className="text-gray-500">Model:</span> {item.model_number}</p>}
                                        </div>
                                      </div>

                                      {/* Purchase Info */}
                                      <div className="space-y-2">
                                        <h4 className="font-semibold text-purple-800 text-sm">Purchase Info</h4>
                                        <div className="space-y-1 text-sm">
                                          {item.purchase_date && <p><span className="text-gray-500">Date:</span> {formatDate(item.purchase_date)}</p>}
                                          {item.purchase_price > 0 && <p><span className="text-gray-500">Price:</span> {formatCurrency(item.purchase_price)}</p>}
                                          {item.supplier && <p><span className="text-gray-500">Supplier:</span> {item.supplier}</p>}
                                        </div>
                                      </div>

                                      {/* Maintenance */}
                                      <div className="space-y-2">
                                        <h4 className="font-semibold text-purple-800 text-sm">Maintenance</h4>
                                        <div className="space-y-1 text-sm">
                                          {item.last_maintenance && <p><span className="text-gray-500">Last:</span> {formatDate(item.last_maintenance)}</p>}
                                          {item.next_maintenance && <p><span className="text-gray-500">Next:</span> {formatDate(item.next_maintenance)}</p>}
                                          {item.notes && <p><span className="text-gray-500">Notes:</span> {item.notes}</p>}
                                        </div>
                                      </div>
                                    </div>
                                  </TableCell>
                                </TableRow>
                              )}
                            </Fragment>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-between items-center mt-4 bg-white/80 backdrop-blur-sm rounded-lg p-3">
                  <p className="text-sm text-gray-600">
                    Showing {startItem}-{endItem} of {totalCount} items
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                      disabled={currentPage === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => p + 1)}
                      disabled={currentPage >= totalPages - 1}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* ========== GRID VIEW ========== */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {loading ? (
                <div className="col-span-full flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-white" />
                </div>
              ) : equipment.length === 0 ? (
                <div className="col-span-full text-center py-12 text-white bg-white/10 backdrop-blur-sm rounded-xl">
                  <div className="flex flex-col items-center gap-2">
                    <Package className="h-8 w-8 text-white/60" />
                    <p className="text-white">No equipment found.</p>
                    <Button variant="link" onClick={clearFilters} className="text-white underline">
                      Clear filters
                    </Button>
                  </div>
                </div>
              ) : (
                equipment.map((item) => (
                  <Card key={item.id} className="border-purple-200/40 bg-white/90 backdrop-blur-sm shadow-lg hover:shadow-xl transition-all">
                    <CardContent className="p-5">
                      {/* Header */}
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-3">
                          <div className="p-3 rounded-lg bg-purple-100">
                            <Package className="h-6 w-6 text-purple-700" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="font-bold text-gray-800">{item.name}</h3>
                            </div>
                            <p className="text-xs text-gray-500">{item.category || 'Uncategorized'}</p>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => toggleExpanded(item.id)}
                          >
                            {expandedItems.has(item.id) ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleEdit(item)}>
                            <Pencil className="h-3.5 w-3.5 text-purple-700" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleDelete(item.id)}>
                            <Trash2 className="h-3.5 w-3.5 text-red-600" />
                          </Button>
                        </div>
                      </div>

                      {/* Quick Info */}
                      <div className="space-y-2 text-sm mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Status:</span>
                          {getStatusBadge(item.status)}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Condition:</span>
                          {getConditionBadge(item.condition)}
                        </div>
                        {item.location && (
                          <div className="flex items-center gap-1 text-gray-600">
                            <MapPin className="h-3 w-3" /> {item.location}
                          </div>
                        )}
                        {item.assigned_to && (
                          <div className="flex items-center gap-1 text-gray-600">
                            <User className="h-3 w-3" /> {item.assigned_to}
                          </div>
                        )}
                      </div>

                      {/* Expanded details */}
                      {expandedItems.has(item.id) && (
                        <div className="mt-4 pt-4 border-t border-purple-100">
                          <div className="space-y-2 text-xs">
                            {item.serial_number && (
                              <p><span className="text-gray-500">Serial:</span> {item.serial_number}</p>
                            )}
                            {item.model_number && (
                              <p><span className="text-gray-500">Model:</span> {item.model_number}</p>
                            )}
                            {item.manufacturer && (
                              <p><span className="text-gray-500">Manufacturer:</span> {item.manufacturer}</p>
                            )}
                            {item.purchase_date && (
                              <p><span className="text-gray-500">Purchased:</span> {formatDate(item.purchase_date)}</p>
                            )}
                            {item.purchase_price > 0 && (
                              <p><span className="text-gray-500">Price:</span> {formatCurrency(item.purchase_price)}</p>
                            )}
                            {item.next_maintenance && (
                              <p><span className="text-gray-500">Next Maint:</span> {formatDate(item.next_maintenance)}</p>
                            )}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </main>
      </div>

      {/* Add/Edit Equipment Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white/95 backdrop-blur-xl border-purple-200">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-purple-700 to-blue-700 bg-clip-text text-transparent">
              {editingItem ? 'Edit Equipment' : 'Add New Equipment'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6 py-4">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid grid-cols-3 mb-4">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="purchase">Purchase & Location</TabsTrigger>
                <TabsTrigger value="maintenance">Maintenance & Notes</TabsTrigger>
              </TabsList>

              {/* Basic Info Tab */}
              <TabsContent value="basic" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Equipment Name *</Label>
                    <Input id="name" name="name" value={formData.name} onChange={handleInputChange} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="category">Category</Label>
                    <Select onValueChange={(v) => handleSelectChange('category', v)} value={formData.category}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORIES.map(cat => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="serial_number">Serial Number</Label>
                    <Input id="serial_number" name="serial_number" value={formData.serial_number} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model_number">Model Number</Label>
                    <Input id="model_number" name="model_number" value={formData.model_number} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="manufacturer">Manufacturer</Label>
                    <Input id="manufacturer" name="manufacturer" value={formData.manufacturer} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Input id="description" name="description" value={formData.description} onChange={handleInputChange} />
                  </div>
                </div>
              </TabsContent>

              {/* Purchase & Location Tab */}
              <TabsContent value="purchase" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="status">Status</Label>
                    <Select onValueChange={(v) => handleSelectChange('status', v)} value={formData.status}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        {STATUSES.map(s => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="condition">Condition</Label>
                    <Select onValueChange={(v) => handleSelectChange('condition', v)} value={formData.condition}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select condition" />
                      </SelectTrigger>
                      <SelectContent>
                        {CONDITIONS.map(c => (
                          <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="purchase_date">Purchase Date</Label>
                    <Input id="purchase_date" name="purchase_date" type="date" value={formData.purchase_date} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="purchase_price">Purchase Price</Label>
                    <Input id="purchase_price" name="purchase_price" type="number" step="0.01" value={formData.purchase_price} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="supplier">Supplier</Label>
                    <Input id="supplier" name="supplier" value={formData.supplier} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Input id="location" name="location" value={formData.location} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="assigned_to">Assigned To</Label>
                    <Input id="assigned_to" name="assigned_to" value={formData.assigned_to} onChange={handleInputChange} />
                  </div>
                </div>
              </TabsContent>

              {/* Maintenance & Notes Tab */}
              <TabsContent value="maintenance" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="last_maintenance">Last Maintenance</Label>
                    <Input id="last_maintenance" name="last_maintenance" type="date" value={formData.last_maintenance} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="next_maintenance">Next Maintenance</Label>
                    <Input id="next_maintenance" name="next_maintenance" type="date" value={formData.next_maintenance} onChange={handleInputChange} />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="notes">Notes</Label>
                    <Textarea id="notes" name="notes" value={formData.notes} onChange={handleInputChange} rows={4} />
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white">
                {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {editingItem ? 'Update Equipment' : 'Save Equipment'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Footer />
    </>
  );
}