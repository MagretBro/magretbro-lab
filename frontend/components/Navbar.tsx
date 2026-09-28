import Link from "next/link";

const navLinks = [
  { label: "Главная", href: "/" },
  { label: "Обо мне", href: "/about" },
  { label: "Аналитика", href: "/analytics" },
  { label: "AI", href: "/ai" },
  { label: "Проекты", href: "/projects" },
  { label: "Контакты", href: "/contacts" },
];

export default function Navbar() {
  return (
    <header className="fixed top-0 left-0 w-full bg-white shadow-sm z-50">
      <nav className="container flex items-center justify-between h-16">
        <Link href="/" className="text-xl font-bold text-gray-900">
          Маргарита Бородина
        </Link>
        <ul className="flex space-x-6 text-sm font-medium">
          {navLinks.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="text-gray-700 hover:text-blue-600 transition-colors"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
