import {
  ArrowUpDown,
  Combine,
  FileCode2,
  FileDown,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileType2,
  Hash,
  Image as ImageIcon,
  Lock,
  LockOpen,
  Minimize2,
  Presentation,
  RotateCw,
  ScanText,
  Scissors,
  Stamp,
  Table2,
  Trash2,
  Type,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  "pdf-to-word": FileType2,
  "pdf-to-jpeg": FileImage,
  "pdf-to-png": ImageIcon,
  "pdf-to-searchable": ScanText,
  "pdf-to-text": Type,
  "pdf-extract-images": ImageIcon,
  "pdf-to-single-pages": FileDown,
  "merge-pdf": Combine,
  "split-pdf": Scissors,
  "extract-pages": FileText,
  "delete-pages": Trash2,
  "reorder-pages": ArrowUpDown,
  "compress-pdf": Minimize2,
  "rotate-pdf": RotateCw,
  "protect-pdf": Lock,
  "unlock-pdf": LockOpen,
  "page-numbers": Hash,
  "watermark-pdf": Stamp,
  "pdf-to-excel": Table2,
  "word-to-pdf": FileText,
  "word-to-jpeg": FileImage,
  "word-to-png": ImageIcon,
  "word-to-text": Type,
  "word-to-html": FileCode2,
  "image-to-pdf": FileText,
  "image-to-word": FileType2,
  "image-to-text": ScanText,
  "image-convert": ImageIcon,
  "image-resize": ArrowUpDown,
  "image-compress": Minimize2,
  "image-rotate": RotateCw,
  "excel-to-pdf": FileText,
  "powerpoint-to-pdf": Presentation,
  "csv-to-excel": FileSpreadsheet,
  "excel-to-csv": FileSpreadsheet,
  "text-to-pdf": FileText,
  "html-to-pdf": FileCode2,
};

export function ToolIcon({
  toolId,
  className = "h-5 w-5",
  strokeWidth = 1.9,
}: {
  toolId: string;
  className?: string;
  strokeWidth?: number;
}) {
  const Icon = ICONS[toolId] ?? FileText;
  return <Icon className={className} strokeWidth={strokeWidth} aria-hidden="true" />;
}

export function FileKindIcon({ name, className = "h-5 w-5" }: { name: string; className?: string }) {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (["pdf"].includes(ext)) return <FileText className={className} aria-hidden="true" />;
  if (["doc", "docx", "rtf", "odt"].includes(ext)) return <FileType2 className={className} aria-hidden="true" />;
  if (["xls", "xlsx", "csv"].includes(ext)) return <FileSpreadsheet className={className} aria-hidden="true" />;
  if (["ppt", "pptx"].includes(ext)) return <Presentation className={className} aria-hidden="true" />;
  if (["html", "htm", "md", "txt"].includes(ext)) return <FileCode2 className={className} aria-hidden="true" />;
  if (["jpg", "jpeg", "png", "webp", "heic", "heif", "gif", "bmp", "tif", "tiff"].includes(ext)) {
    return <FileImage className={className} aria-hidden="true" />;
  }
  return <FileText className={className} aria-hidden="true" />;
}
