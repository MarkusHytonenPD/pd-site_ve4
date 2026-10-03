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
    /* Palkin taustalla on heron kopio (.site-header::before), joka on yhtä
       suuri kuin hero ja siirretään niin, että palkki näyttää täsmälleen ne
       heron pikselit jotka ovat sen alla -- palkki näyttää läpinäkyvältä mutta
       peittää alle liukuvat herotekstit. Kun heron alareuna saavuttaa palkin,
       kopio lukittuu ja heron alaosa jää palkiksi. Kuvaa tai väriä ei vaihdeta
       missään vaiheessa, joten välähdystä ei synny.
       Laskennalliset arvot kopioidaan, jotta sivukohtaiset muunnelmat
       (rajaus, yritys-sivun kevyempi sävy) tulevat mukaan sellaisinaan. */
    const copyHero = () => {
      const cs = getComputedStyle(hero);
      header.style.setProperty('--hero-bg', cs.backgroundImage);
      header.style.setProperty('--hero-bg-pos', cs.backgroundPosition);
      header.style.setProperty('--hero-bg-size', cs.backgroundSize);
      header.style.setProperty('--hero-h', hero.offsetHeight + 'px');
      header.style.setProperty('--header-h', header.offsetHeight + 'px');
    };

    /* Alasivuilla lukitus heron alareunaan. Etusivun gradientti haipuu alas
       lähes läpinäkyväksi (0,14), joten alareuna olisi valikolle liian vaalea
       (kontrasti 3,6-4,9:1). Siellä lukitaan heti alkuun: palkkiin jää heron
       tumma yläosa (0,70), sama tummansininen kuin ennenkin. */
    const lockAtTop = !hero.classList.contains('page-hero');
    const syncHeader = () => {
      const lockAt = lockAtTop
        ? -hero.offsetTop
        : hero.offsetHeight - header.offsetHeight;
      const behind = -hero.getBoundingClientRect().top;   // heron rivi palkin yläreunassa
      header.style.setProperty('--hero-top', Math.min(behind, lockAt) + 'px');
      /* varjo vasta kun palkki on lukittu ja sivua on vieritetty */
      header.classList.toggle('scrolled', window.scrollY > 0 && behind >= lockAt);
    };

    window.addEventListener('resize', () => { copyHero(); syncHeader(); });
    copyHero();
    window.addEventListener('scroll', syncHeader, { passive: true });
    syncHeader();   /* myös heti latauksessa, jos sivu avataan ankkuriin */
  }
})();
