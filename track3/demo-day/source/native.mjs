// Places the same editable layout in Spaces or an Artifact Tool presentation.
// The public, stand-alone PowerPoint build is provided by layout.py.
export function placeSlides(presentation, layout, assetFor, start=0, end=layout.length) {
  for (let n=start;n<end;n++) {
    const spec=layout[n];
    const slide=(n===0 && presentation.slides.items.length===1) ? presentation.slides.getItem(0) : presentation.slides.add();
    slide.size={width:1280,height:720};
    slide.background.fill=spec.bg;
    slide.speakerNotes.text=spec.notes;
    for(const item of spec.items) {
      const [left,top,width,height]=item.box;
      const position={left,top,width,height};
      if(item.kind==='text') {
        const shape=slide.shapes.add({name:item.text.slice(0,40),geometry:'textbox',position,
          fill:'none',line:{fill:'none',width:0}});
        shape.text=item.text;
        shape.text.style={fontSize:item.size,typeface:item.font,bold:item.bold,color:item.colour,
          verticalAlignment:'top',wrap:'square',autoFit:'none',insets:0};
        if(item.link)shape.hyperlink={uri:item.link,isExternal:true};
      } else if(item.kind==='image') {
        slide.images.add({...assetFor(item.file),fit:'contain',position,alt:item.alt});
      } else {
        const t=slide.tables.add({rows:item.values.length,columns:item.values[0].length,
          left,top,width,height,columnWidths:item.widths,values:item.values});
        t.borders.assign({width:1,fill:'#354358',style:'solid'});
        for(let i=0;i<item.values.length;i++)for(let j=0;j<item.values[i].length;j++){
          const cell=t.getCell(i,j);const ln=item.links[i+','+j];
          cell.fill=i===0?'#263648':'#151B32';
          cell.text.style={fontSize:item.size,typeface:item.font,bold:i===0,color:(i===0||ln)?'#ABE8CA':'#FBF9F2',
            verticalAlignment:'middle',wrap:'none',insets:{left:8,right:4,top:3,bottom:3}};
          if(ln)slide.shapes.add({name:item.values[i][j]+' · block explorer',geometry:'rect',
            position:{left:left+item.widths.slice(0,j).reduce((a,b)=>a+b,0),
              top:top+i*item.rowh,width:item.widths[j],height:item.rowh},
            fill:'none',line:{fill:'none',width:0},hyperlink:{uri:ln,isExternal:true}});
        }
      }
    }
  }
}
