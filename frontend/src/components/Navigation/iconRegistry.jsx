import {
  BadgeCheck,
  Bell,
  Briefcase,
  Building,
  Building2,
  Calendar,
  CalendarCheck,
  CalendarDays,
  ChartLine,
  CheckCircle,
  CircleDollarSign,
  Clock,
  Contact2,
  Database,
  Download,
  Euro,
  FileDown,
  FileSignature,
  FileText,
  FileUp,
  IdCard,
  Landmark,
  Leaf,
  Link,
  Info,
  Lock,
  List as ListIcon,
  Mail,
  MapPin,
  Package,
  Pencil,
  Plus,
  Puzzle,
  Upload,
  Receipt,
  Save,
  Search,
  Settings,
  ShieldCheck,
  AlertTriangle,
  Tag,
  Trash2,
  User,
  Users,
  Wrench,
  Zap,
  ExternalLink,
  UserMinus,
  UserCheck,
  TrendingUp,
  TrendingDown,
  Check,
  Coins,
  Folder,
  Gauge,
  LayoutDashboard,
  Circle,
} from 'lucide-react';

const ICONS = {
  'external-link': ExternalLink,
  'user-minus': UserMinus,
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
  clock: Clock,
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
  link: Link,
  lock: Lock,
  plus: Plus,
  'alert-triangle': AlertTriangle,
  'badge-check': BadgeCheck,
  bell: Bell,
  'shield-check': ShieldCheck,
  'check-circle': CheckCircle,
  leaf: Leaf,
  mail: Mail,
  envelope: Mail,
  receipt: Receipt,
  save: Save,
  search: Search,
  wrench: Wrench,
  'money-bill-wave': CircleDollarSign,
  cog: Settings,
  'user-tie': Contact2,
  'building-columns': Landmark,
  tag: Tag,
  puzzle: Puzzle,
  'user-check': UserCheck,
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
  'file-signature': FileSignature,
  check: Check,
  coins: Coins,
  euro: Euro,
  folder: Folder,
  'tachometer-alt': Gauge,
  dashboard: LayoutDashboard,
};

// Icon names are kebab-case identifiers; anything else (an emoji) is shown as text.
const ICON_NAME = /^[a-z][a-z0-9-]*$/;
const warned = new Set();

export function renderIcon(iconName, options = {}) {
  if (!iconName) return null;
  const { size = 18, className, fallbackClassName = 'nav-emoji-icon' } = options;
  let Icon = ICONS[iconName];
  if (!Icon && ICON_NAME.test(iconName)) {
    // Unknown name: a neutral icon instead of the raw name as text.
    if (import.meta.env.DEV && !warned.has(iconName)) {
      warned.add(iconName);
      console.warn(`[iconRegistry] icona non registrata: "${iconName}"`);
    }
    Icon = Circle;
  }
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
