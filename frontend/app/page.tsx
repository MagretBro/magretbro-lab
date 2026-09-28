import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        {/* Hero Section */}
        <section className="container text-center" style={{ paddingTop: "6rem" }}>
          <h1 className="text-5xl font-extrabold tracking-tight mb-4">
            Маргарита Бородина
          </h1>
          <p className="text-xl text-gray-600 mb-6">
            Data Analyst / Product Analyst
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-10">
            Data Analytics • Product Analytics • A/B Testing • SQL • Python
          </p>
          <a href="#directions" className="btn btn-primary">
            Узнать больше
          </a>
        </section>

        {/* Directions Section */}
        <section id="directions" className="container">
          <h2 className="section-title text-center">Направления</h2>
          <div className="grid grid-cols-4">
            <div className="card text-center">
              <h3 className="text-xl font-semibold mb-2">SQL & Data</h3>
              <p className="text-sm text-gray-600">
                Работа с большими данными, построение запросов, очистка и трансформация данных.
              </p>
            </div>
            <div className="card text-center">
              <h3 className="text-xl font-semibold mb-2">Product Analytics</h3>
              <p className="text-sm text-gray-600">
                Анализ поведения пользователей, метрики продукта, оптимизация воронок.
              </p>
            </div>
            <div className="card text-center">
              <h3 className="text-xl font-semibold mb-2">A/B Testing</h3>
              <p className="text-sm text-gray-600">
                Планирование экспериментов, статистический анализ, выводы и рекомендации.
              </p>
            </div>
            <div className="card text-center">
              <h3 className="text-xl font-semibold mb-2">Automation</h3>
              <p className="text-sm text-gray-600">
                Автоматизация отчётности и аналитических процессов с помощью Python.
              </p>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
