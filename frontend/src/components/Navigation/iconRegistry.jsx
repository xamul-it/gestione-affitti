import {
  BadgeCheck,
  Briefcase,
  Building,
  Building2,
  Calendar,
  Database,
  FileText,
  Info,
  Lock,
  List as ListIcon,
  MapPin,
  Package,
  Pencil,
  Plus,
  Settings,
  ShieldCheck,
  Trash2,
  User,
  Users,
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
  pencil: Pencil,
  trash: Trash2,
  'file-text': FileText,
  info: Info,
  lock: Lock,
  plus: Plus,
  'badge-check': BadgeCheck,
  'shield-check': ShieldCheck,
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
