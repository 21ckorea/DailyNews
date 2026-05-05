const items = document.querySelectorAll('div.news_wrap');
if (items.length > 0) {
    const item = items[0];
    console.log("Item container: div.news_wrap");
    console.log("Title selector:", item.querySelector('a.news_tit') ? 'a.news_tit' : 'not found');
    console.log("Press selector:", item.querySelector('a.info.press') ? 'a.info.press' : 'not found');
    console.log("Date selector:", item.querySelector('span.info') ? 'span.info' : 'not found');
    console.log("Image selector:", item.querySelector('img.thumb') ? 'img.thumb' : 'not found');
} else {
    console.log("No div.news_wrap found. Checking li.bx...");
    const bx_items = document.querySelectorAll('li.bx');
    console.log("li.bx count:", bx_items.length);
}
