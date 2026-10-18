/* Render only diagrams near the viewport, including those revealed inside details. */
mermaid.initialize({
  startOnLoad: false,
  securityLevel: 'strict',
  htmlLabels: false,
  markdownAutoWrap: false,
  theme: 'base',
  fontFamily: 'system-ui, "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif',
  themeVariables: {
    primaryColor: '#edf4ee', primaryTextColor: '#202e35', primaryBorderColor: '#568678',
    lineColor: '#536771', secondaryColor: '#f7f3e8', tertiaryColor: '#fffefa',
    fontSize: '16px'
  },
  flowchart: {htmlLabels: false, useMaxWidth: true, curve: 'linear'},
  sequence: {useMaxWidth: true, actorMargin: 40, wrap: true},
  suppressErrorRendering: true
});
let diagramQueue = Promise.resolve();
function enqueueDiagram(figure) {
  if (figure.dataset.queued) return;
  figure.dataset.queued = 'true';
  diagramQueue = diagramQueue.then(async () => {
    const canvas = figure.querySelector('.diagram-canvas');
    try {
      const definition = figure.querySelector('.diagram-source').textContent;
      const {svg} = await mermaid.render(figure.dataset.diagramId, definition);
      canvas.innerHTML = svg;
      const graphic = canvas.querySelector('svg');
      graphic.style.width = `${graphic.viewBox.baseVal.width}px`;
      graphic.style.maxWidth = 'none';
      figure.dataset.rendered = 'true';
    } catch (error) {
      canvas.textContent = '図を表示できませんでした。下のテキストで内容を確認できます。';
      figure.querySelector('.diagram-text').open = true;
      figure.dataset.rendered = 'error';
      console.error('Diagram rendering failed:', figure.dataset.diagramId, error);
    }
  });
}
const figures = document.querySelectorAll('figure.diagram');
figures.forEach((figure, index) => {figure.dataset.diagramId = `cs-diagram-${index}`;});
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        observer.unobserve(entry.target);
        enqueueDiagram(entry.target);
      }
    }
  }, {rootMargin: '300px'});
  figures.forEach(figure => observer.observe(figure));
} else {
  figures.forEach(enqueueDiagram);
}
