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
     saman sivun ankkuri (esim. #asiakirjat) jätti valikon auki peittämään näkymän. */
  mainNav.addEventListener('click', (e) => {
    if (e.target.closest('a')) closeNav();
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.site-header')) closeNav();
  });

  if (header && hero) {
    /* Alasivuilla palkin tausta on sivun oma herokuva ja -sävy, ei etusivun
       järvikuva. Kopioidaan laskennalliset arvot, jotta sivukohtaiset
       muunnelmat (esim. yritys-sivun kevyempi sävy) tulevat mukaan sellaisinaan. */
    if (hero.classList.contains('page-hero')) {
      const heroStyle = getComputedStyle(hero);
      header.style.setProperty('--header-bg', heroStyle.backgroundImage);
      header.style.setProperty('--header-bg-pos', heroStyle.backgroundPosition);
    }

    /* Palkki muuttuu läpinäkymättömäksi heti kun herotekstit alkavat liukua sen
       alle. Aiemmin raja oli koko heron alareuna, joten palkki oli läpinäkyvä
       koko heron matkan ja tekstit menivät logon ja valikon kanssa päällekkäin.
       Etusivun herossa ei ole näkyvää tekstiä, joten siellä raja on yhä alareuna. */
    /* Herotekstit alkavat heti palkin alareunan alta (.page-hero:n yläpadding
       on palkin korkeus + 4.5rem, ja laatikko alkaa -76px), joten käytännössä
       raja on ensimmäinen vieritetty pikseli. Lasketaan se silti tekstin
       paikasta, ettei raja hajoa jos paddingia muutetaan. */
    const heroText = hero.querySelector('.container');
    const syncHeader = () => {
      const scrolledPast = heroText
        ? window.scrollY > Math.max(0,
            heroText.getBoundingClientRect().top + window.scrollY - header.offsetHeight)
        : hero.getBoundingClientRect().bottom <= header.offsetHeight;
      header.classList.toggle('scrolled', scrolledPast);
    };
    window.addEventListener('scroll', syncHeader, { passive: true });
    syncHeader();   /* myös heti latauksessa, jos sivu avataan ankkuriin */
  }
})();
