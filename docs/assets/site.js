(function () {
  var root = document.documentElement;
  function get(key) { try { return localStorage.getItem(key); } catch (err) { return null; } }
  function set(key, value) { try { localStorage.setItem(key, value); } catch (err) { /* private window */ } }

  var pick = get("lang");
  if (root.lang === "en" && pick && pick !== "en") {
    var saved = document.querySelector('a[data-lang="' + pick + '"]');
    if (saved) { location.replace(saved.getAttribute("href")); return; }
  }

  var button = document.getElementById("motion");
  function apply(on) {
    root.classList.toggle("still", on);
    if (button) {
      button.textContent = on ? button.dataset.play : button.dataset.pause;
      button.setAttribute("aria-pressed", String(on));
    }
  }
  apply(get("still") === "1");
  if (button) button.addEventListener("click", function () { var on = !root.classList.contains("still"); apply(on); set("still", on ? "1" : "0"); });

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
})();
