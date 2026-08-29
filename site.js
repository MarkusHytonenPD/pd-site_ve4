/* PlanDisain — yhteinen skripti kaikille sivuille.
   Oli aiemmin kopioituna jokaisen sivun <script>-lohkoon; ainoa ero oli
   hero-elementin valitsin, joka on etusivulla .hero ja alasivuilla .page-hero. */
(() => {
  const header = document.querySelector('.site-header');
  const hero = document.querySelector('.hero, .page-hero');
  const navToggle = document.querySelector('.nav-toggle');
  const mainNav = document.querySelector('.main-nav');

  if (!navToggle || !mainNav) return;

  const closeNav = () => {
    mainNav.classList.remove('open');
    navToggle.classList.remove('open');
    navToggle.setAttribute('aria-expanded', 'false');
  };

  navToggle.addEventListener('click', () => {
    const isOpen = mainNav.classList.toggle('open');
    navToggle.classList.toggle('open', isOpen);
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });

  /* Valikko sulkeutuu myös linkkiä painettaessa. Aiemmin sulkeutuminen
     kuunteli vain klikkauksia yläpalkin ULKOPUOLELLA, joten mobiilissa
     saman sivun ankkuri (#palvelut) jätti valikon auki peittämään näkymän. */
  mainNav.addEventListener('click', (e) => {
    if (e.target.closest('a')) closeNav();
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.site-header')) closeNav();
  });

  if (header && hero) {
    const syncHeader = () => {
      header.classList.toggle(
        'scrolled',
        hero.getBoundingClientRect().bottom <= header.offsetHeight
      );
    };
    window.addEventListener('scroll', syncHeader, { passive: true });
    syncHeader();   /* myös heti latauksessa, jos sivu avataan ankkuriin */
  }
})();
