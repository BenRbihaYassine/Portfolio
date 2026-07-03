
//  DÉTECTION DES TRANSACTIONS SUSPECTES — main.js
// =========================================================
 
document.addEventListener('DOMContentLoaded', () => {
 
  // --- Burger menu mobile ---
  const burger    = document.getElementById('burger');
  const mobileNav = document.getElementById('mobile-nav');
 
  if (burger && mobileNav) {
    burger.addEventListener('click', () => {
      burger.classList.toggle('open');
      mobileNav.classList.toggle('open');
    });
  }
 
  // --- Fermer le menu mobile si on clique ailleurs ---
  document.addEventListener('click', (e) => {
    if (burger && mobileNav) {
      if (!burger.contains(e.target) && !mobileNav.contains(e.target)) {
        burger.classList.remove('open');
        mobileNav.classList.remove('open');
      }
    }
  });
 
  // --- Animation d'apparition des éléments ---
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
 
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
 
});