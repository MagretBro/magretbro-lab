export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-16">
      <div className="container text-center py-8">
        <p className="text-sm text-gray-600">
          © {new Date().getFullYear()} Маргарита Бородина. Все права защищены.
        </p>
      </div>
    </footer>
  );
}
