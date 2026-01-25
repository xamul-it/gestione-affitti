import {
  BadgeCheck,
  Briefcase,
  Building,
  Building2,
  Calendar,
  CalendarCheck,
  CalendarDays,
  ChartLine,
  CheckCircle,
  CircleDollarSign,
  Database,
  Download,
  Euro,
  FileDown,
  FileSignature,
  FileText,
  FileUp,
  IdCard,
  Leaf,
  Info,
  Lock,
  List as ListIcon,
  MapPin,
  Package,
  Pencil,
  Plus,
  Upload,
  Receipt,
  Search,
  Settings,
  ShieldCheck,
  AlertTriangle,
  Trash2,
  User,
  Users,
  Wrench,
  Zap,
} from 'lucide-react';

const ICONS = {
  users: Users,
  user: User,
  building: Building,
  'building-2': Building2,
  'map-pin': MapPin,
  list: ListIcon,
  briefcase: Briefcase,
  zap: Zap,
  settings: Settings,
  package: Package,
  database: Database,
  calendar: Calendar,
  'calendar-alt': CalendarDays,
  'calendar-check': CalendarCheck,
  'chart-line': ChartLine,
  'euro-sign': Euro,
  'file-contract': FileSignature,
  'file-down': FileDown,
  'file-up': FileUp,
  pencil: Pencil,
  trash: Trash2,
  download: Download,
  upload: Upload,
  'file-text': FileText,
  'id-card': IdCard,
  info: Info,
  lock: Lock,
  plus: Plus,
  'alert-triangle': AlertTriangle,
  'badge-check': BadgeCheck,
  'shield-check': ShieldCheck,
  'check-circle': CheckCircle,
  leaf: Leaf,
  receipt: Receipt,
  search: Search,
  wrench: Wrench,
  'money-bill-wave': CircleDollarSign,
  cog: Settings,
};

export function renderIcon(iconName, options = {}) {
  if (!iconName) return null;
  const { size = 18, className, fallbackClassName = 'nav-emoji-icon' } = options;
  const Icon = ICONS[iconName];
  if (Icon) {
    return <Icon size={size} strokeWidth={1.7} className={className} aria-hidden="true" />;
  }
  return (
    <span className={fallbackClassName} aria-hidden="true">
      {iconName}
    </span>
  );
}

export { ICONS };
