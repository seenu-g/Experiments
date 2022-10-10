function CategoryList(props) {

  const items = props.list;
    return (
      <>
        <h2>{props.name}</h2>
        <ul> {items.map((item) => 
              <li key = {item.id}> {item.name}</li>)}
        </ul>
      </>
    );
  }
  export default CategoryList;