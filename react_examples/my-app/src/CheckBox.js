export const CheckBox = (props) => {
    const {title, id, label,value,isChecked,changed} = props
  
    return (
      <div className="CheckBox">
        {title}
          <input
            id= {id}
            value= {value}
            checked={isChecked}
            onChange={changed}
            type="checkbox"
          />
        <label for={id}>{label}</label>
      </div>
    );
  }

