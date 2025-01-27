import cl from "./ButtonForScroll.module.css"

const ButtonForScroll = ({ icon: Icon, handleBtnScroll, direction }) => {

    const aboba = () => {
        handleBtnScroll(direction)
    }

    return (
        <div className={cl.container}>
            <button className={cl.btn} onClick={aboba}>
                {Icon && <Icon />}
            </button>

        </div>
    )
}

export default ButtonForScroll