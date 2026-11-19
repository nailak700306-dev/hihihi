(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Header: solid background once the page scrolls
  var header = document.getElementById('header');
  function onScroll() { if (header) header.classList.toggle('scrolled', window.scrollY > 30); }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Mobile menu
  var burger = document.getElementById('burger');
  var menu = document.getElementById('menu');
  if (burger && menu) {
    burger.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      burger.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        menu.classList.remove('open'); burger.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false'); document.body.style.overflow = '';
      });
    });
  }

  // Split headings into words for the reveal animation (keeps inline <em>)
  document.querySelectorAll('.split').forEach(function (el) {
    var nodes = Array.prototype.slice.call(el.childNodes);
    el.innerHTML = '';
    var i = 0;
    nodes.forEach(function (n) {
      var isEm = n.nodeType === 1;
      var text = n.textContent;
      text.split(/(\s+)/).forEach(function (part) {
        if (!part) return;
        if (/^\s+$/.test(part)) { el.appendChild(document.createTextNode(' ')); return; }
        var w = document.createElement('span'); w.className = 'w';
        var inner = document.createElement(isEm ? 'em' : 'span');
        inner.textContent = part;
        inner.style.transitionDelay = (i++ * 0.045) + 's';
        if (isEm) { var s = document.createElement('span'); s.appendChild(inner); s.style.transitionDelay = inner.style.transitionDelay; w.appendChild(s); }
        else w.appendChild(inner);
        el.appendChild(w);
      });
    });
  });

  // Count-up numbers
  function countUp(el) {
    var end = parseInt(el.getAttribute('data-count'), 10);
    var suffix = el.getAttribute('data-suffix') || '';
    if (reduce) { el.textContent = end + suffix; return; }
    var start = null, dur = 1600;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min(1, (ts - start) / dur);
      var e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(end * e) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // Reveal on scroll
  var targets = document.querySelectorAll('.reveal, .split, .level, [data-count]');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('in');
        if (en.target.hasAttribute('data-count')) countUp(en.target);
        io.unobserve(en.target);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    targets.forEach(function (t) { io.observe(t); });
  } else {
    targets.forEach(function (t) { t.classList.add('in'); });
  }

  // Contact form: open the visitor's mail app with a pre-filled message
  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (form.website && form.website.value) return; // honeypot
      var name = form.nom.value.trim();
      var mail = form.email.value.trim();
      var need = form.besoin.value;
      var msg = form.message.value.trim();
      var subject = 'Demande FD CONSULTING — ' + need + (name ? ' — ' + name : '');
      var body = msg + '\n\n—\n' + name + '\n' + mail;
      window.location.href = 'mailto:fabricedepaz@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    });
  }
})();
