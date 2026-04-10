'use client';
import Link from 'next/link';
import { useState } from 'react';
import { Menu, X, Smartphone } from 'lucide-react';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl text-[#01696f]">
          <Smartphone size={22} />
          EgyptPhones
        </Link>
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          <Link href="/devices" className="text-gray-700 hover:text-[#01696f] transition-colors">
            Devices
          </Link>
          <Link href="/devices?brand=samsung" className="text-gray-700 hover:text-[#01696f] transition-colors">
            Samsung
          </Link>
          <Link href="/devices?brand=apple" className="text-gray-700 hover:text-[#01696f] transition-colors">
            Apple
          </Link>
          <Link href="/devices?brand=xiaomi" className="text-gray-700 hover:text-[#01696f] transition-colors">
            Xiaomi
          </Link>
        </div>
        <button
          className="md:hidden p-2 rounded-md hover:bg-gray-100"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-gray-100 px-4 py-3 flex flex-col gap-3 text-sm">
          <Link href="/devices" onClick={() => setOpen(false)} className="text-gray-700">Devices</Link>
          <Link href="/devices?brand=samsung" onClick={() => setOpen(false)} className="text-gray-700">Samsung</Link>
          <Link href="/devices?brand=apple" onClick={() => setOpen(false)} className="text-gray-700">Apple</Link>
          <Link href="/devices?brand=xiaomi" onClick={() => setOpen(false)} className="text-gray-700">Xiaomi</Link>
        </div>
      )}
    </nav>
  );
}
