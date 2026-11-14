(function () {
  var root = document.documentElement;
  function get(key) { try { return localStorage.getItem(key); } catch (err) { return null; } }
  function set(key, value) { try { localStorage.setItem(key, value); } catch (err) { /* private window */ } }

  var pick = get("lang");
  if (root.lang === "en" && pick && pick !== "en") {
    var saved = document.querySelector('a[data-lang="' + pick + '"]');
    if (saved) { location.replace(saved.getAttribute("href")); return; }
  }

  document.querySelectorAll("a[data-lang]").forEach(function (link) {
    link.addEventListener("click", function () { set("lang", link.dataset.lang); });
  });

  var menus = document.querySelectorAll(".menu");
  menus.forEach(function (menu) {
    menu.addEventListener("toggle", function () {
      if (menu.open) menus.forEach(function (other) { if (other !== menu) other.open = false; });
    });
  });
  document.addEventListener("click", function (ev) {
    menus.forEach(function (menu) { if (menu.open && !menu.contains(ev.target)) menu.open = false; });
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    menus.forEach(function (menu) { if (menu.open) { menu.open = false; menu.querySelector("summary").focus(); } });
  });

  // Step bar: highlight the section in view and keep its chip visible.
  var chips = Array.prototype.slice.call(document.querySelectorAll(".bar a"));
  if (chips.length && "IntersectionObserver" in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var on = chips.filter(function (c) { return c.hash === "#" + entry.target.id; })[0];
        if (!on) return;
        chips.forEach(function (c) { if (c === on) c.setAttribute("aria-current", "true"); else c.removeAttribute("aria-current"); });
        var list = on.closest("ol");
        list.scrollTo({ left: on.parentElement.offsetLeft - 60, behavior: "smooth" });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    chips.forEach(function (c) { var t = document.getElementById(c.hash.slice(1)); if (t) spy.observe(t); });
  }

  // Tap a screenshot to zoom. Esc closes; arrows or swipe move between screenshots.
  var text = document.getElementById("zoom-text");
  if (!text) return;
  var label = text.dataset;
  document.addEventListener("click", function (ev) {
    var img = ev.target.closest(".ph:not(.noimg) img");
    if (!img || img.closest("a") || img.closest(".lb")) return;
    var all = Array.prototype.slice.call(document.querySelectorAll(".ph:not(.noimg) img")).filter(function (i) { return !i.closest("a") && i.offsetParent; });
    var at = Math.max(0, all.indexOf(img));
    var back = document.activeElement;
    var box = document.createElement("div");
    box.className = "lb";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML = '<img alt=""><button class="x" type="button"></button><button class="pv" type="button">←</button><button class="nx" type="button">→</button><p aria-live="polite"></p>';
    var big = box.querySelector("img"), cap = box.querySelector("p");
    box.querySelector(".x").textContent = "×";
    box.querySelector(".x").setAttribute("aria-label", label.close);
    box.querySelector(".pv").setAttribute("aria-label", label.prev);
    box.querySelector(".nx").setAttribute("aria-label", label.next);
    function show(i) {
      at = (i + all.length) % all.length;
      big.src = all[at].src;
      big.alt = all[at].alt;
      box.setAttribute("aria-label", all[at].alt || label.close);
      cap.textContent = (all[at].alt ? all[at].alt + " · " : "") + label.of.replace("{n}", at + 1).replace("{total}", all.length);
    }
    function close() { box.remove(); document.removeEventListener("keydown", key); document.body.style.overflow = ""; if (back && back.focus) back.focus(); }
    function key(e) {
      if (e.key === "Escape") close();
      else if (e.key === "ArrowRight") show(at + 1);
      else if (e.key === "ArrowLeft") show(at - 1);
      else if (e.key === "Tab") { var b = box.querySelectorAll("button"); var first = b[0], last = b[b.length - 1]; if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); } }
    }
    box.addEventListener("click", function (e) { if (e.target === box || e.target === big) close(); });
    box.querySelector(".x").addEventListener("click", close);
    box.querySelector(".pv").addEventListener("click", function () { show(at - 1); });
    box.querySelector(".nx").addEventListener("click", function () { show(at + 1); });
    var startX = null;
    big.addEventListener("touchstart", function (e) { startX = e.touches[0].clientX; }, { passive: true });
    big.addEventListener("touchend", function (e) { if (startX === null) return; var dx = e.changedTouches[0].clientX - startX; if (Math.abs(dx) > 50) show(at + (dx < 0 ? 1 : -1)); startX = null; });
    document.addEventListener("keydown", key);
    document.body.appendChild(box);
    document.body.style.overflow = "hidden";
    show(at);
    box.querySelector(".x").focus();
  });
})();
